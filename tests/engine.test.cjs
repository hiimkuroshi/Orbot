const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../orbot/engine.js'), 'utf8');
const captureSource = fs.readFileSync(path.join(__dirname, '../orbot/capture.js'), 'utf8');
const copy = value => JSON.parse(JSON.stringify(value));

class Clock {
    now = Date.parse('2026-10-20T00:00:00Z');
    sequence = 0;
    jobs = new Map();
    add(fn, delay, interval = 0) {
        const id = ++this.sequence;
        this.jobs.set(id, { fn, due: this.now + delay, interval });
        return id;
    }
    async flush() { for (let i = 0; i < 15; i++) await Promise.resolve(); }
    async advance(duration, keepAlive = null) {
        const end = this.now + duration;
        await this.flush();
        for (let guard = 0; guard < 10000; guard++) {
            const next = [...this.jobs.entries()].filter(([, job]) => job.due <= end)
                .sort((a, b) => a[1].due - b[1].due)[0];
            if (!next) break;
            const [id, job] = next;
            this.now = job.due;
            if (keepAlive) keepAlive();
            if (job.interval) job.due += job.interval;
            else this.jobs.delete(id);
            job.fn();
            await this.flush();
        }
        this.now = end;
        await this.flush();
    }
}

function quest(id, key = 'WATCH_VIDEO', target = 14) {
    return {
        id, config: {
            messages: { questName: `Quest ${id}` }, expiresAt: '2027-01-01T00:00:00Z',
            taskConfigV2: { tasks: { [key]: { target, applications: [{ id: '123456789' }] } } },
            rewardsConfig: { rewards: [{ type: 1 }, { type: 4, orbQuantity: 200 }] }
        }, userStatus: { enrolledAt: '2026-10-19', progress: {} }
    };
}

async function fixture(quests, options = {}) {
    const clock = new Clock();
    const calls = [];
    const eventLog = [];
    const listeners = new Map();
    const realGame = { id: 'real', pid: 7 };
    const store = { quests: new Map(quests.map(item => [item.id, item])), getQuest(id) { return this.quests.get(id); } };
    const user = { id: 'owner', username: 'Test account' };
    const games = {
        getRunningGames: () => [realGame], getGameForPID: pid => pid === 7 ? realGame : undefined,
        getVisibleRunningGames: () => [realGame], getCandidateGames: () => [realGame],
        getVisibleGame: () => realGame, getRunningDiscordApplicationIds: () => new Set(['real'])
    };
    const originalGames = games.getRunningGames;
    const dispatcher = {
        dispatch(event) {
            calls.push({ dispatch: event });
            if (event.type === 'QUESTS_ENROLL_SUCCESS') {
                const status = event.enrolledQuestUserStatus;
                const item = store.getQuest(status.questId);
                if (item) item.userStatus = status;
            }
        },
        subscribe(event, callback) { if (!listeners.has(event)) listeners.set(event, new Set()); listeners.get(event).add(callback); },
        unsubscribe(event, callback) { listeners.get(event)?.delete(callback); }
    };
    const handle = async (method, request) => {
        calls.push({ method, ...request });
        if (options.request) {
            const result = await options.request(method, request);
            if (result !== undefined) return result;
        }
        if (request.url === '/users/@me') return { status: 200, body: { id: user.id } };
        if (method === 'get') return { status: 200, body: [{ name: 'Fixture Game', executables: [{ os: 'win32', name: 'game.exe' }] }] };
        const [,, id, operation] = request.url.split('/');
        const item = store.getQuest(id);
        if (operation === 'enroll') {
            item.userStatus.enrolledAt = new Date(clock.now).toISOString();
            return { status: 200, body: { type: 'success' } };
        }
        if (operation === 'claim-reward') {
            assert.equal(request.body.platform, 4, 'Use Discord desktop claim platform');
            item.userStatus.claimedAt = new Date(clock.now).toISOString();
            return { status: 200, body: {} };
        }
        const key = Object.keys(item.config.taskConfigV2.tasks)[0];
        const target = item.config.taskConfigV2.tasks[key].target;
        item.userStatus.progress[key] = { value: request.body.timestamp };
        if (request.body.timestamp >= target) item.userStatus.completedAt = new Date(clock.now).toISOString();
        return { status: 200, body: { progress: item.userStatus.progress, completed_at: item.userStatus.completedAt } };
    };
    const api = { get: request => handle('get', request), post: request => handle('post', request), del() {} };
    const FakeDate = class extends Date {
        constructor(...args) { super(...(args.length ? args : [clock.now])); }
        static now() { return clock.now; }
    };
    const context = vm.createContext({
        Map, Set, WeakMap, AbortController, console, Date: FakeDate,
        setTimeout: (fn, delay) => clock.add(fn, delay), clearTimeout: id => clock.jobs.delete(id),
        setInterval: (fn, delay) => clock.add(fn, delay, delay), clearInterval: id => clock.jobs.delete(id),
        __orbotCapture: { modules: new Set([store, { getCurrentUser: () => user, getUser() {} }, games, dispatcher, api]), loaders: new Set() }
    });
    vm.runInContext(source, context);
    const engine = context.__orbot;
    await engine.discover();
    return { engine, clock, calls, store, user, games, originalGames, listeners, context, api, eventLog,
        advance: duration => clock.advance(duration, () => { eventLog.push(...engine.snapshot().events); }) };
}

test('discovers current V2 tasks, sums Orbs after other reward types, rejects console-only', async () => {
    const video = quest('video');
    video.config.taskConfig = { tasks: { PLAY_ON_XBOX: { target: 999 } } };
    video.config.rewardsConfig.rewards.push({ type: 4, orbQuantity: 50 });
    const consoleOnly = quest('console', 'PLAY_ON_XBOX');
    const noOrbs = quest('no-orbs'); noOrbs.config.rewardsConfig.rewards = [{ type: 1 }];
    const expired = quest('expired'); expired.config.expiresAt = '2020-01-01';
    const f = await fixture([video, consoleOnly, noOrbs, expired]);
    const rows = copy(f.engine.snapshot().quests);
    assert.equal(rows.length, 3);
    assert.equal(rows[0].taskKey, 'WATCH_VIDEO');
    assert.equal(rows[0].orbs, 250);
    assert.equal(rows[0].application, '123456789');
    assert.equal(rows[1].runnable, false);
    assert.equal(rows[2].runnable, false);
});

test('enrolls, completes video based on server acknowledgement, and optionally claims', async () => {
    const item = quest('video'); item.userStatus.enrolledAt = null;
    const f = await fixture([item]);
    f.engine.start({ ids: ['video'], autoClaim: true });
    await f.advance(22000);
    const row = f.engine.snapshot().quests[0];
    assert.equal(row.status, 'claimed');
    assert.equal(row.completed, true);
    assert.equal(f.engine.snapshot().running, false);
    assert.ok(f.calls.some(call => call.url?.endsWith('/enroll')));
    assert.ok(f.calls.some(call => call.url?.endsWith('/claim-reward')));
});

test('one queue completes and claims three videos in order without restarting', async () => {
    const f = await fixture(['first', 'second', 'third'].map(id => quest(id, 'WATCH_VIDEO', 7)));
    const ids = ['first', 'second', 'third', 'first'];
    f.engine.start({ ids, autoClaim: true });
    ids.splice(1); // The run must own its ordered list, independently of the caller.
    await f.advance(8000);
    let snapshot = f.engine.snapshot();
    assert.equal(snapshot.running, true, 'Finishing the first Quest must not end the run');
    assert.equal(snapshot.activeId, 'second');
    assert.deepEqual(copy(snapshot.queue.ids), ['first', 'second', 'third']);
    await f.advance(15000);
    snapshot = f.engine.snapshot();
    assert.equal(snapshot.running, false);
    assert.equal(snapshot.queue.status, 'finished');
    assert.ok(snapshot.quests.every(row => row.claimed));
    assert.deepEqual(f.calls.filter(call => call.method === 'post').map(call => call.url), [
        '/quests/first/video-progress', '/quests/first/claim-reward',
        '/quests/second/video-progress', '/quests/second/claim-reward',
        '/quests/third/video-progress', '/quests/third/claim-reward'
    ]);
});

test('a game is cleaned up and claimed before the following video starts', async () => {
    const item = quest('game', 'PLAY_ON_DESKTOP', 3);
    const f = await fixture([item, quest('video', 'WATCH_VIDEO', 7)]);
    f.engine.start({ ids: ['game', 'video'], autoClaim: true });
    await f.clock.flush();
    item.userStatus.progress.PLAY_ON_DESKTOP = { value: 3 };
    for (const listener of f.listeners.get('QUESTS_SEND_HEARTBEAT_SUCCESS')) {
        listener({ questId: 'game', userStatus: item.userStatus });
    }
    await f.advance(2000);
    assert.equal(f.engine.snapshot().activeId, 'video');
    assert.equal(f.games.getRunningGames, f.originalGames);
    assert.equal(f.listeners.get('QUESTS_SEND_HEARTBEAT_SUCCESS').size, 0);
    await f.advance(8000);
    assert.ok(f.engine.snapshot().quests.every(row => row.claimed));
});

test('an individual Quest error does not discard subsequent queue entries', async () => {
    const f = await fixture([quest('bad', 'WATCH_VIDEO', 7), quest('good', 'WATCH_VIDEO', 7)], {
        request: async (_method, request) => {
            if (request.url === '/quests/bad/video-progress') throw { status: 400 };
        }
    });
    f.engine.start({ ids: ['bad', 'good'], autoClaim: true });
    await f.advance(16000);
    const snapshot = f.engine.snapshot();
    assert.equal(snapshot.quests[0].status, 'failed');
    assert.equal(snapshot.quests[1].status, 'claimed');
    assert.equal(snapshot.queue.status, 'finished');
});

test('a normal claim error leaves a claim-only retry and continues the next Quest', async () => {
    let rejected = true;
    const f = await fixture([quest('first', 'WATCH_VIDEO', 7), quest('next', 'WATCH_VIDEO', 7)], {
        request: async (_method, request) => {
            if (rejected && request.url === '/quests/first/claim-reward') throw { status: 400 };
        }
    });
    f.engine.start({ ids: ['first', 'next'], autoClaim: true });
    await f.advance(16000);
    const snapshot = f.engine.snapshot();
    assert.equal(snapshot.quests[0].status, 'claim_required');
    assert.equal(snapshot.quests[0].completed, true);
    assert.equal(snapshot.quests[1].claimed, true);
    const progressCalls = f.calls.filter(call => call.url?.endsWith('/video-progress')).length;
    rejected = false;
    f.engine.start({ ids: ['first', 'next'], autoClaim: true });
    await f.clock.flush();
    assert.ok(f.engine.snapshot().quests.every(row => row.claimed));
    assert.equal(f.calls.filter(call => call.url?.endsWith('/video-progress')).length, progressCalls);
});

test('fatal claim errors preserve pending entries and report a blocked queue', async () => {
    const f = await fixture([quest('first', 'WATCH_VIDEO', 7), quest('next', 'WATCH_VIDEO', 7)], {
        request: async (_method, request) => {
            if (request.url.endsWith('/claim-reward')) throw { status: 403 };
        }
    });
    f.engine.start({ ids: ['first', 'next'], autoClaim: true });
    await f.advance(16000);
    const snapshot = f.engine.snapshot();
    assert.equal(snapshot.running, false);
    assert.equal(snapshot.queue.status, 'blocked');
    assert.match(snapshot.queue.error, /403/);
    assert.deepEqual(copy(snapshot.queue.ids), ['first', 'next']);
    assert.equal(snapshot.quests[0].status, 'claim_required');
    assert.equal(snapshot.quests[1].status, 'queued');
    assert.ok(!f.calls.some(call => call.url?.includes('/quests/next/')));
});

test('the claiming state remains active until the response, then advances to the next Quest', async () => {
    let confirm;
    const f = await fixture([quest('first', 'WATCH_VIDEO', 7), quest('next', 'WATCH_VIDEO', 7)], {
        request: async (_method, request) => {
            if (request.url === '/quests/first/claim-reward') return new Promise(resolve => { confirm = resolve; });
        }
    });
    f.engine.start({ ids: ['first', 'next'], autoClaim: true });
    await f.advance(8000);
    const waiting = f.engine.snapshot();
    assert.equal(waiting.running, true);
    assert.equal(waiting.activeId, 'first');
    assert.equal(waiting.quests[0].status, 'claiming');
    assert.ok(!f.calls.some(call => call.url?.includes('/quests/next/')));
    confirm({ status: 200, body: {} });
    await f.clock.flush();
    assert.equal(f.engine.snapshot().activeId, 'next');
    await f.advance(8000);
    assert.ok(f.engine.snapshot().quests.every(row => row.claimed));
});

test('stopping and resuming a queue never repeats a successfully claimed Quest', async () => {
    const f = await fixture(['first', 'second', 'third'].map(id => quest(id, 'WATCH_VIDEO', 7)));
    f.engine.start({ ids: ['first', 'second', 'third'], autoClaim: true });
    await f.advance(8000);
    const stopped = f.engine.stop();
    assert.equal(stopped.queue.status, 'stopped');
    assert.deepEqual(copy(stopped.queue.ids), ['first', 'second', 'third']);
    f.engine.start({ ids: stopped.queue.ids, autoClaim: true });
    await f.advance(16000);
    assert.ok(f.engine.snapshot().quests.every(row => row.claimed));
    assert.equal(f.calls.filter(call => call.url === '/quests/first/claim-reward').length, 1);
});

test('auto-claim disabled still advances through all Quests and leaves rewards unclaimed', async () => {
    const f = await fixture(['first', 'second'].map(id => quest(id, 'WATCH_VIDEO', 7)));
    f.engine.start({ ids: ['first', 'second'], autoClaim: false });
    await f.advance(16000);
    const snapshot = f.engine.snapshot();
    assert.equal(snapshot.queue.status, 'finished');
    assert.ok(snapshot.quests.every(row => row.completed && !row.claimed));
    assert.ok(!f.calls.some(call => call.url?.endsWith('/claim-reward')));
    assert.throws(() => f.engine.start({ ids: ['first', 'second'], autoClaim: false }), /Chưa chọn/);
    f.engine.start({ ids: ['first', 'second'], autoClaim: true });
    await f.clock.flush();
    assert.ok(f.engine.snapshot().quests.every(row => row.claimed));
    assert.equal(f.calls.filter(call => call.url?.endsWith('/video-progress')).length, 2);
});

test('accepted local timestamps never count as server-confirmed completion', async () => {
    const f = await fixture([quest('video')], { request: async (method, request) => {
        if (request.url.endsWith('/video-progress')) return { status: 200, body: {} };
    } });
    f.engine.start({ ids: ['video'], autoClaim: true });
    await f.advance(120000);
    const row = f.engine.snapshot().quests[0];
    assert.equal(row.completed, false);
    assert.equal(row.status, 'failed');
    assert.ok(!f.calls.some(call => call.url?.endsWith('/claim-reward')));
});

test('desktop play preserves real processes, reads heartbeats beyond two minutes, and restores methods', async () => {
    const item = quest('game', 'PLAY_ON_DESKTOP', 160);
    const f = await fixture([item]);
    f.engine.start({ ids: ['game'], autoClaim: false });
    await f.clock.flush();
    assert.equal(f.games.getRunningGames().length, 2);
    const interval = f.clock.add(() => {
        const value = (item.userStatus.progress.PLAY_ON_DESKTOP?.value || 0) + 20;
        item.userStatus.progress.PLAY_ON_DESKTOP = { value };
        for (const listener of f.listeners.get('QUESTS_SEND_HEARTBEAT_SUCCESS') || []) {
            listener({ questId: 'game', userStatus: { progress: item.userStatus.progress } });
        }
    }, 20000, 20000);
    await f.advance(165000);
    f.clock.jobs.delete(interval);
    assert.equal(f.engine.snapshot().quests[0].status, 'completed');
    assert.equal(f.games.getRunningGames, f.originalGames);
    assert.equal(f.games.getRunningGames().length, 1);
    assert.equal(f.listeners.get('QUESTS_SEND_HEARTBEAT_SUCCESS').size, 0);
});

test('Stop restores state immediately and prevents the next queued Quest', async () => {
    const f = await fixture([quest('game', 'PLAY_ON_DESKTOP', 900), quest('video')]);
    f.engine.start({ ids: ['game', 'video'], autoClaim: false });
    await f.clock.flush();
    f.engine.stop();
    await f.advance(20000);
    assert.equal(f.games.getRunningGames, f.originalGames);
    assert.equal(f.engine.snapshot().running, false);
    assert.ok(f.engine.snapshot().quests.every(row => row.status === 'stopped'));
    assert.ok(!f.calls.some(call => call.url?.includes('/quests/video/')));
});

test('losing the desktop app lease cancels the engine and restores the game', async () => {
    const f = await fixture([quest('game', 'PLAY_ON_DESKTOP', 900)]);
    f.engine.start({ ids: ['game'] });
    await f.clock.flush();
    await f.clock.advance(17000);
    assert.equal(f.engine.snapshot().running, false);
    assert.equal(f.games.getRunningGames, f.originalGames);
});

test('account changes stop the queue without sending requests for the new account', async () => {
    const f = await fixture([quest('video'), quest('second')]);
    f.engine.start({ ids: ['video', 'second'] });
    await f.clock.flush();
    f.user.id = 'another-owner';
    await f.advance(10000);
    assert.equal(f.engine.snapshot().running, false);
    assert.ok(!f.calls.some(call => call.url?.includes('/video-progress')));
});

test('HTTP 403 stops subsequent Quests; 429 obeys the server wait before retry', async () => {
    let count = 0;
    const f = await fixture([quest('video'), quest('second')], { request: async (_method, request) => {
        if (request.url.endsWith('/video-progress')) {
            count++;
            if (count === 1) throw { status: 429, body: { retry_after: 5 } };
            throw { status: 403 };
        }
    } });
    f.engine.start({ ids: ['video', 'second'] });
    await f.advance(11000);
    assert.equal(count, 1);
    await f.advance(3000);
    assert.equal(count, 2);
    assert.equal(f.engine.snapshot().running, false);
    assert.ok(!f.calls.some(call => call.url?.includes('/quests/second/')));
});

test('suspended accounts are blocked before enrollment', async () => {
    const f = await fixture([quest('video')]);
    f.store.questAccessSuspendedUntil = '2027-01-01';
    await f.engine.discover();
    assert.throws(() => f.engine.start({ ids: ['video'] }), /hạn chế/);
    assert.ok(!f.calls.some(call => call.method === 'post'));
});

test('a stalled game fails, cleans up, and does not falsely mark completion', async () => {
    const f = await fixture([quest('game', 'PLAY_ON_DESKTOP', 900)]);
    f.engine.start({ ids: ['game'] });
    await f.advance(123000);
    assert.equal(f.engine.snapshot().quests[0].status, 'failed');
    assert.equal(f.engine.snapshot().quests[0].completed, false);
    assert.equal(f.games.getRunningGames, f.originalGames);
});

test('raw enrollment response is dispatched to Discord before starting desktop play', async () => {
    const item = quest('game', 'PLAY_ON_DESKTOP', 900);
    item.userStatus.enrolledAt = null;
    const f = await fixture([item], { request: async (_method, request) => {
        if (request.url.endsWith('/enroll')) return {
            status: 200, body: { quest_id: 'game', enrolled_at: '2026-10-20T00:00:00Z', progress: {} }
        };
    } });
    f.engine.start({ ids: ['game'] });
    await f.clock.flush();
    assert.ok(item.userStatus.enrolledAt);
    assert.equal(f.games.getRunningGames().length, 2);
    assert.ok(f.calls.some(call => call.dispatch?.type === 'QUESTS_ENROLL_SUCCESS'));
    f.engine.stop();
});

test('native Quest fetch is awaited before publishing refreshed results', async () => {
    const f = await fixture([]);
    function nativeFetch() {
        const marker = 'QUESTS_FETCH_CURRENT_QUESTS_BEGIN';
        f.store.quests.set('new-video', quest('new-video'));
        return Promise.resolve(marker);
    }
    f.context.__orbotCapture.modules.add({ nativeFetch });
    const snapshot = await f.engine.discover();
    assert.equal(snapshot.quests.length, 1);
    assert.equal(snapshot.quests[0].id, 'new-video');
});

test('a failure halfway through game patching restores methods already changed', async () => {
    const f = await fixture([quest('game', 'PLAY_ON_DESKTOP', 900)]);
    Object.defineProperty(f.games, 'getVisibleGame', { value: f.games.getVisibleGame, writable: false });
    f.engine.start({ ids: ['game'] });
    await f.clock.flush();
    assert.equal(f.engine.snapshot().quests[0].status, 'failed');
    assert.equal(f.games.getRunningGames, f.originalGames);
});

test('confirmed claims are not repeated while Discord store is stale', async () => {
    const f = await fixture([quest('video')], { request: async (_method, request) => {
        if (request.url.endsWith('/claim-reward')) return { status: 200, body: {} };
    } });
    f.engine.start({ ids: ['video'], autoClaim: true });
    await f.advance(22000);
    assert.equal(f.engine.snapshot().quests[0].claimed, true);
    await f.engine.discover();
    assert.equal(f.engine.snapshot().quests[0].claimed, true);
    assert.throws(() => f.engine.start({ ids: ['video'], autoClaim: true }), /Chưa chọn/);
    assert.equal(f.calls.filter(call => call.url?.endsWith('/claim-reward')).length, 1);
});

test('early loader capture collects modules even when require.c is absent', () => {
    const context = vm.createContext({ console });
    vm.runInContext(captureSource, context);
    vm.runInContext(`
        globalThis.webpackChunkdiscord_app = [];
        globalThis.webpackChunkdiscord_app.push = function(chunk) {
            for (const factory of Object.values(chunk[1])) {
                const module = {exports: {}};
                factory(module, module.exports, function require() {});
            }
        };
        webpackChunkdiscord_app.push([[1], {example(module) { module.exports = {getQuest() {}}; }}]);
    `, context);
    assert.equal(vm.runInContext('__orbotCapture.modules.size', context), 1);
    vm.runInContext('__orbotCapture.dispose()', context);
    assert.equal(context.__orbotCapture, undefined);
});

test('lazy namespace proxies cannot impersonate stores by manufacturing probed methods', async () => {
    const f = await fixture([quest('video')]);
    const lazy = new Proxy({}, { get() { return function placeholder() {}; } });
    const modules = f.context.__orbotCapture.modules;
    f.context.__orbotCapture.modules = new Set([lazy, ...modules]);
    const result = await f.engine.discover();
    assert.equal(result.ready, true);
    assert.equal(result.quests.length, 1);
    assert.equal(result.diagnostics.questStore, true);
    assert.equal(result.diagnostics.api, true);
});

test('named Discord store instances outrank plain lookalikes and expose inherited getters', async () => {
    const f = await fixture([quest('video')]);
    const bait = { getQuest() {}, quests: new Map() };
    class QuestStore {
        static displayName = 'QuestStore';
        get quests() { return f.store.quests; }
        getQuest(id) { return f.store.getQuest(id); }
    }
    class UserStore {
        static displayName = 'UserStore';
        getCurrentUser() { return f.user; }
        getUser() {}
    }
    const modules = f.context.__orbotCapture.modules;
    f.context.__orbotCapture.modules = new Set([bait, new QuestStore(), new UserStore(), ...modules]);
    const result = await f.engine.discover();
    assert.equal(result.ready, true);
    assert.equal(result.quests[0].id, 'video');
});

test('raw HTTP helpers are excluded even when they precede the authenticated REST client', async () => {
    const f = await fixture([quest('video')]);
    let rawCalls = 0;
    const raw = {
        Request() {}, get() { rawCalls++; return { status: 200, body: '<!DOCTYPE html>' }; },
        post() { rawCalls++; }, put() {}, patch() {}, del() {}
    };
    const modules = f.context.__orbotCapture.modules;
    f.context.__orbotCapture.modules = new Set([raw, ...modules]);
    const result = await f.engine.discover();
    assert.equal(result.ready, true);
    assert.equal(result.diagnostics.apiVerified, true);
    assert.equal(rawCalls, 0);
});

test('URL-style authenticated clients use their verified signature for Quest calls', async () => {
    const f = await fixture([quest('video')]);
    const rest = {
        get(url) {
            if (typeof url !== 'string') throw new TypeError('Expected URL');
            return f.api.get({ url });
        },
        post(url, options) {
            assert.equal(typeof url, 'string');
            return f.api.post({ url, body: options?.body });
        }, put() {}, patch() {}, del() {}
    };
    f.context.__orbotCapture.modules.delete(f.api);
    f.context.__orbotCapture.modules.add(rest);
    const result = await f.engine.discover();
    assert.equal(result.ready, true);
    assert.equal(result.diagnostics.apiStyle, 'url');
    f.engine.start({ ids: ['video'], autoClaim: true });
    await f.advance(22000);
    assert.equal(f.engine.snapshot().quests[0].status, 'claimed');
});

test('HTML responses fail once, stop subsequent Quests and never appear raw in the log', async () => {
    const f = await fixture([quest('video'), quest('second')], { request: async (_method, request) => {
        if (request.url.endsWith('/video-progress')) return {
            status: 200, body: '<!DOCTYPE html><html><head><meta content="https://discord.com/[object Object]">',
            headers: { 'content-type': 'text/html' }
        };
    } });
    f.engine.start({ ids: ['video', 'second'] });
    await f.advance(22000);
    const state = f.engine.snapshot();
    assert.equal(state.quests[0].status, 'failed');
    assert.equal(state.running, false);
    assert.equal(f.calls.filter(call => call.url?.endsWith('/video-progress')).length, 1);
    assert.ok(!f.calls.some(call => call.url?.includes('/quests/second/')));
    const events = [...f.eventLog, ...state.events];
    assert.ok(!events.some(event => /<!DOCTYPE|<meta|\[object Object\]/i.test(event.message)));
    assert.ok(events.some(event => event.message.includes('HTML')));
});

test('unverified clients cannot start Quests even if they expose the expected methods', async () => {
    const f = await fixture([quest('video')]);
    let mutations = 0;
    const wrongAccount = {
        get() { return { status: 200, body: { id: 'another-account' } }; },
        post() { mutations++; }, put() {}, patch() {}, del() {}
    };
    f.context.__orbotCapture.modules.delete(f.api);
    f.context.__orbotCapture.modules.add(wrongAccount);
    const state = await f.engine.discover();
    assert.equal(state.ready, false);
    assert.equal(state.diagnostics.apiVerified, false);
    assert.throws(() => f.engine.start({ ids: ['video'] }), /chưa sẵn sàng/);
    assert.equal(mutations, 0);
});
