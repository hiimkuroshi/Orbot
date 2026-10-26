/* Orbot's in-memory Discord adapter. Intentionally limited to video and desktop-play Quests. */
(() => {
    "use strict";
    if (globalThis.__orbot?.version === "0.1.3") return;
    globalThis.__orbot?.shutdown?.();
    const state = { modules: {}, rows: new Map(), confirmed: new Map(), events: [], active: null, lease: Date.now(), apiOwner: null, apiStyle: null,
        queue: { runId: 0, owner: null, ids: [], status: "idle", error: "" } };
    const supported = ["WATCH_VIDEO", "WATCH_VIDEO_ON_MOBILE", "PLAY_ON_DESKTOP", "PLAY_ON_DESKTOP_V2"];
    const finite = value => Number.isFinite(Number(value)) ? Math.max(0, Number(value)) : 0;
    const values = value => value instanceof Map ? [...value.values()] : Object.values(value || {});
    const stamp = value => value ? Date.parse(value) : NaN;
    const camel = value => {
        if (Array.isArray(value)) return value.map(camel);
        if (!value || typeof value !== "object") return value;
        return Object.fromEntries(Object.entries(value).map(([key, item]) => [
            key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase()), camel(item)
        ]));
    };
    const html = value => typeof value === "string" && /<(?:!doctype|html|head|meta)(?:\s|>)/i.test(value);
    const errorText = (cause, status) => {
        if (html(cause?.message) || html(cause?.body) || html(cause?.response?.text)) {
            return "Discord trả về trang HTML thay vì dữ liệu API. Hãy kết nối lại Orbot.";
        }
        return String(cause?.message || (status ? `Discord trả về HTTP ${status}.` : "Lỗi kết nối với Discord."))
            .replace(/\s+/g, " ").slice(0, 220);
    };
    const log = (message, level = "info") => {
        const text = html(String(message)) ? "Phản hồi HTML không hợp lệ từ Discord; hãy kết nối lại Orbot." : String(message);
        state.events.push({ time: new Date().toISOString(), level, message: text.slice(0, 500) });
        if (state.events.length > 250) state.events.shift();
    };
    function moduleCandidates() {
        const roots = new Set(globalThis.__orbotCapture?.modules || []);
        const loaders = new Set(globalThis.__orbotCapture?.loaders || []);
        const chunks = globalThis.webpackChunkdiscord_app;
        if (chunks?.push) {
            try {
                const marker = `orbot_${Date.now()}`;
                chunks.push([[marker], {}, require => { loaders.add(require); }]);
            } catch { /* A locked runtime can be captured on an explicit reload. */ }
        }
        for (const require of loaders) {
            for (const module of Object.values(require?.c || {})) {
                if (module?.exports) roots.add(module.exports);
            }
        }
        const vencord = globalThis.Vencord?.Webpack;
        if (vencord) {
            for (const name of ["QuestsStore", "QuestStore", "UserStore", "RunningGameStore"]) {
                try { roots.add(vencord.findStore?.(name)); } catch { /* Optional adapter. */ }
            }
            for (const keys of [["get", "post", "del"], ["dispatch", "subscribe", "unsubscribe"]]) {
                try { roots.add(vencord.findByProps?.(...keys)); } catch { /* Optional adapter. */ }
            }
        }
        const candidates = new Set();
        function visit(value, depth) {
            if (!value || !["object", "function"].includes(typeof value) || candidates.has(value)) return;
            candidates.add(value);
            if (!depth) return;
            let keys;
            try { keys = Object.keys(value).slice(0, 150); } catch { return; }
            for (const key of keys) {
                try { visit(value[key], depth - 1); } catch { /* Lazy exports may throw. */ }
            }
        }
        for (const root of roots) visit(root, 2);
        return [...candidates];
    }
    function resolveModules() {
        const candidates = moduleCandidates();
        // Inspect declared methods: probing arbitrary properties can match lazy namespace proxies.
        const descriptor = (value, key) => {
            try {
                for (let depth = 0; value && depth < 5; depth++, value = Object.getPrototypeOf(value)) {
                    const result = Object.getOwnPropertyDescriptor(value, key);
                    if (result) return result;
                }
            } catch { /* An inaccessible lazy namespace is not a store. */ }
            return null;
        };
        const methods = (value, names) => names.every(name => typeof descriptor(value, name)?.value === "function");
        const displayName = value => {
            const constructor = descriptor(value, "constructor")?.value;
            return descriptor(constructor, "displayName")?.value;
        };
        const store = (names, required, valid) => candidates.find(value => names.includes(displayName(value)) && methods(value, required))
            || candidates.find(value => methods(value, required) && (!valid || valid(value)));
        const quests = store(["QuestStore", "QuestsStore"], ["getQuest"], value => {
            try {
                return value.quests instanceof Map || methods(value, ["getQuests"]) || methods(value, ["getAllQuests"]);
            } catch { return false; }
        });
        // A raw HTTP library has these verbs too, but cannot attach the Discord session.
        const apiCandidates = candidates.filter(value => (methods(value, ["get", "post", "put", "patch"])
            || methods(value, ["get", "post", "del"])) && !descriptor(value, "Request")
            && !descriptor(value, "getXHR") && !descriptor(value, "getQuest"));
        const dispatcher = quests?._dispatcher;
        state.modules = {
            quests,
            user: store(["UserStore"], ["getCurrentUser", "getUser"]),
            games: store(["RunningGameStore"], ["getRunningGames", "getGameForPID"]),
            dispatcher: methods(dispatcher, ["dispatch", "subscribe", "unsubscribe"]) ? dispatcher
                : candidates.find(value => methods(value, ["dispatch", "subscribe", "unsubscribe"])),
            api: null, apiCandidates,
            fetchQuests: candidates.find(value => {
                if (typeof value !== "function") return false;
                try { return value.toString().includes("QUESTS_FETCH_CURRENT_QUESTS_BEGIN"); }
                catch { return false; }
            })
        };
        state.apiOwner = state.apiStyle = null;
        state.diagnostics = {
            questStore: Boolean(state.modules.quests), userStore: Boolean(state.modules.user),
            api: Boolean(state.modules.api), games: Boolean(state.modules.games),
            dispatcher: Boolean(state.modules.dispatcher), capture: Boolean(globalThis.__orbotCapture),
            capturedModules: globalThis.__orbotCapture?.modules.size || 0,
            candidates: candidates.length
        };
    }
    function invokeApi(client, style, method, url, body) {
        return style === "url"
            ? client[method](url, body === undefined ? undefined : { body })
            : client[method]({ url, ...(body === undefined ? {} : { body }) });
    }
    async function selectApi() {
        const owner = currentUser()?.id;
        if (!owner) return;
        const deadline = Date.now() + 5000;
        for (const client of state.modules.apiCandidates.slice(0, 4)) {
            for (const style of ["object", "url"]) {
                if (Date.now() >= deadline) { state.diagnostics.apiVerified = false; return; }
                let timeout;
                try {
                    const response = await Promise.race([
                        invokeApi(client, style, "get", "/users/@me"),
                        new Promise((_, reject) => { timeout = setTimeout(() => reject(new Error("timeout")), 1800); })
                    ]);
                    if (currentUser()?.id !== owner) return;
                    if (response?.status !== 200 || !response.body || typeof response.body !== "object"
                        || String(response.body.id) !== String(owner)) continue;
                    state.modules.api = client;
                    state.apiOwner = String(owner);
                    state.apiStyle = style;
                    state.diagnostics.api = true;
                    state.diagnostics.apiVerified = true;
                    state.diagnostics.apiStyle = style;
                    return;
                } catch { /* An invalid client/signature must never be used for a Quest mutation. */ }
                finally { clearTimeout(timeout); }
            }
        }
        state.diagnostics.apiVerified = false;
    }
    function questList() {
        const store = state.modules.quests;
        return values(store?.quests || store?.getQuests?.() || store?.getAllQuests?.());
    }
    function currentUser() { return state.modules.user?.getCurrentUser?.(); }
    function accessBlocked() {
        const store = state.modules.quests;
        const until = store?.questAccessSuspendedUntil
            || store?.getQuestAccessSuspendedUntil?.() || currentUser()?.questAccessSuspendedUntil;
        return Number.isFinite(stamp(until)) && stamp(until) > Date.now();
    }
    function ready() {
        return Boolean(state.modules.quests && state.modules.api && state.apiOwner
            && String(currentUser()?.id) === state.apiOwner);
    }
    function normalize(quest) {
        const config = quest.config || {};
        const modern = config.taskConfigV2 || config.task_config_v2;
        const legacy = config.taskConfig || config.task_config;
        const tasks = values(modern?.tasks).length ? modern.tasks : (legacy?.tasks || {});
        const taskKey = supported.find(key => tasks instanceof Map ? tasks.has(key) : tasks[key]);
        const task = taskKey ? (tasks instanceof Map ? tasks.get(taskKey) : tasks[taskKey]) : null;
        const application = task?.applications?.[0]?.id || config.application?.id;
        const status = quest.userStatus || quest.user_status || {};
        const rewardList = config.rewardsConfig?.rewards || config.rewards_config?.rewards || [];
        const orbs = rewardList.reduce((sum, reward) => sum + finite(reward.orbQuantity ?? reward.orb_quantity), 0);
        const target = finite(task?.target);
        const progress = finite(status.progress?.[taskKey]?.value ?? status.streamProgressSeconds);
        const expires = config.expiresAt || config.expires_at;
        const starts = config.startsAt || config.starts_at;
        let reason = "";
        if (!orbs) reason = "Không có thưởng Orbs";
        else if (!taskKey) reason = "Loại Quest chưa hỗ trợ";
        else if (!target) reason = "Thiếu thời lượng yêu cầu";
        else if (taskKey.startsWith("PLAY") && (!application || !state.modules.games || !state.modules.dispatcher)) {
            reason = "Chưa tìm thấy bộ nhận diện game";
        }
        else if (stamp(expires) <= Date.now()) reason = "Đã hết hạn";
        else if (stamp(starts) > Date.now()) reason = "Chưa bắt đầu";
        else if (accessBlocked()) reason = "Tài khoản đang bị hạn chế Quests";
        const confirmation = state.confirmed.get(`${currentUser()?.id}:${quest.id}`) || {};
        const claimed = Boolean(status.claimedAt || status.claimed_at || confirmation.claimed);
        const completed = Boolean(status.completedAt || status.completed_at || confirmation.completed);
        return {
            id: String(quest.id), name: String(config.messages?.questName || config.messages?.gameTitle || config.application?.name || quest.id),
            kind: taskKey?.startsWith("WATCH") ? "video" : (taskKey?.startsWith("PLAY") ? "game" : "other"),
            taskKey, application: application ? String(application) : null,
            orbs, target, progress: Math.min(progress, target || progress), expires,
            enrolled: Boolean(status.enrolledAt || status.enrolled_at), completed, claimed,
            runnable: !reason && !claimed, reason,
            status: claimed ? "claimed" : completed ? "completed" : reason ? "unsupported" : "ready"
        };
    }
    function refresh() {
        for (const quest of questList()) {
            const row = normalize(quest);
            if (!row.orbs) continue;
            const previous = state.rows.get(row.id);
            if (previous && row.runnable && !row.completed && !row.claimed) {
                row.status = previous.status;
                row.progress = Math.max(row.progress, previous.progress);
                if (["failed", "stopped", "claim_required"].includes(previous.status)) row.detail = previous.detail;
            }
            state.rows.set(row.id, row);
        }
    }
    function snapshot() {
        state.lease = Date.now();
        const user = currentUser();
        return {
            ready: ready(), running: Boolean(state.active),
            user: user ? { id: String(user.id), name: String(user.globalName || user.username || "Discord") } : null,
            blocked: accessBlocked(), quests: [...state.rows.values()], events: state.events.splice(0),
            activeId: state.active?.questId || null, diagnostics: state.diagnostics || {},
            queue: { ...state.queue, ids: [...state.queue.ids] }
        };
    }
    async function discover() {
        if (state.active) return snapshot();
        resolveModules();
        await selectApi();
        const owner = String(currentUser()?.id || "");
        if (ready() && state.modules.fetchQuests) {
            let timeout;
            try {
                await Promise.race([
                    state.modules.fetchQuests(),
                    new Promise((_, reject) => { timeout = setTimeout(() => reject(new Error("timeout")), 3000); })
                ]);
            } catch { log("Chưa tải mới được Quests; đang đọc dữ liệu sẵn có trong Discord.", "warning"); }
            finally { clearTimeout(timeout); }
        }
        if (String(currentUser()?.id || "") !== owner) {
            state.rows.clear();
            log("Tài khoản vừa thay đổi; hãy quét lại.", "warning");
            return snapshot();
        }
        state.rows.clear(); refresh();
        return snapshot();
    }
    function check(context) {
        if (state.active !== context || context.cancelled) throw new Error("ORBOT_STOPPED");
        if (String(currentUser()?.id) !== context.owner) {
            const error = new Error("Tài khoản Discord đã thay đổi. Đã dừng.");
            error.fatal = true;
            throw error;
        }
        if (accessBlocked()) {
            const error = new Error("Tài khoản đang bị hạn chế Quests.");
            error.fatal = true;
            throw error;
        }
    }
    function wait(context, milliseconds) {
        check(context);
        return new Promise((resolve, reject) => {
            const cancel = () => { clearTimeout(timer); reject(new Error("ORBOT_STOPPED")); };
            const timer = setTimeout(() => {
                context.controller.signal.removeEventListener("abort", cancel);
                try { check(context); resolve(); } catch (error) { reject(error); }
            }, milliseconds);
            context.controller.signal.addEventListener("abort", cancel, { once: true });
        });
    }
    async function request(method, url, body, context) {
        for (let attempt = 0; attempt < 3; attempt++) {
            check(context);
            let timeout;
            try {
                const response = await Promise.race([
                    invokeApi(state.modules.api, state.apiStyle, method, url, body === null ? undefined : body),
                    new Promise((_, reject) => { timeout = setTimeout(() => reject(new Error("Discord không phản hồi.")), 12000); })
                ]);
                check(context);
                if (!Number.isFinite(response?.status)) throw new Error("Discord chưa trả về phản hồi hợp lệ.");
                if (response.status < 200 || response.status >= 300) throw response;
                const contentType = response.headers?.["content-type"] || response.type || "";
                if (html(response.body) || html(response.text) || /text\/html/i.test(contentType)
                    || (response.body != null && typeof response.body !== "object")) {
                    const error = new Error("Discord trả về trang HTML thay vì JSON. Hãy kết nối lại Orbot.");
                    error.fatal = true;
                    throw error;
                }
                const payload = response?.body || {};
                if (payload.captcha_key || /captcha/i.test(String(payload.type || ""))) {
                    const error = new Error("Cần xác minh trực tiếp trong Discord.");
                    error.fatal = true;
                    throw error;
                }
                return payload;
            } catch (cause) {
                check(context);
                const status = Number(cause?.status ?? cause?.statusCode ?? cause?.response?.status);
                const error = new Error(errorText(cause, status));
                error.fatal = cause?.fatal || html(cause?.message) || html(cause?.body)
                    || html(cause?.response?.text) || [401, 403].includes(status);
                if (error.fatal || (status && status !== 429 && status < 500) || attempt === 2) throw error;
                const delay = status === 429
                    ? Math.min(120000, Math.max(1000, finite(cause?.body?.retry_after) * 1000))
                    : (attempt + 1) * 3000;
                log(`Discord yêu cầu chờ; thử lại sau ${Math.ceil(delay / 1000)} giây.`, "warning");
                await wait(context, delay);
            } finally { clearTimeout(timeout); }
        }
    }
    function readServerProgress(row, body) {
        const status = body.userStatus || body.user_status || body;
        const current = state.modules.quests?.getQuest(row.id);
        const currentStatus = current?.userStatus || current?.user_status || {};
        const value = status.progress?.[row.taskKey]?.value ?? currentStatus.progress?.[row.taskKey]?.value;
        if (Number.isFinite(Number(value))) row.progress = Math.min(row.target, finite(value));
        if ((row.target > 0 && finite(value) >= row.target) || status.completedAt || status.completed_at || currentStatus.completedAt || currentStatus.completed_at) {
            row.completed = true;
            row.progress = row.target;
        }
    }
    async function video(row, context) {
        let reported = row.progress;
        const started = Date.now();
        const initial = reported;
        let unchangedSince = Date.now();
        while (!row.completed) {
            await wait(context, 7000);
            const proposed = Math.min(row.target, initial + (Date.now() - started) / 1000);
            const body = await request("post", `/quests/${row.id}/video-progress`, { timestamp: proposed }, context);
            const old = row.progress;
            readServerProgress(row, body);
            // A timestamp being accepted is not proof of completion. Display it as reported progress.
            reported = Math.max(reported, proposed);
            row.progress = Math.max(row.progress, reported);
            if (row.progress > old) unchangedSince = Date.now();
            if (!row.completed && Date.now() - unchangedSince > 90000) {
                throw new Error("Discord chưa xác nhận hoàn thành video. Kiểm tra Quest trong Discord.");
            }
            if (Date.now() - started > (row.target + 180) * 1000) throw new Error("Quest video hết thời gian chờ.");
        }
    }
    function installGame(row, app, context) {
        const store = state.modules.games;
        const pid = Math.floor(100000 + Math.random() * 500000);
        const cleanName = String(app.name || row.name).replace(/[<>:"/\\|?*]/g, "");
        const relative = String(app.executables?.find(item => item.os === "win32")?.name || `${cleanName}.exe`)
            .replace(/>/g, "").replace(/\\/g, "/");
        const exeName = relative.split("/").pop();
        const relativePath = relative.includes("/") ? relative : `${cleanName}/${relative}`;
        const game = {
            id: row.application, name: app.name || row.name, pid, pidPath: [pid],
            exeName, exePath: `c:/program files/${relativePath}`.toLowerCase(),
            cmdLine: `C:\\Program Files\\${relativePath.replace(/\//g, "\\")}`,
            processName: app.name || row.name, hidden: false, isLauncher: false, start: Date.now()
        };
        const originals = new Map();
        const replacements = new Map();
        const cleanup = () => {
            for (const [name, record] of originals) {
                if (store[name] !== replacements.get(name)) continue;
                if (record.own) store[name] = record.fn;
                else delete store[name];
            }
            state.modules.dispatcher.dispatch({ type: "RUNNING_GAMES_CHANGE", removed: [game], added: [], games: store.getRunningGames() });
        };
        context.cleanups.push(cleanup);
        const patch = (name, replacement) => {
            if (typeof store[name] !== "function") return;
            originals.set(name, { own: Object.hasOwn(store, name), fn: store[name] });
            replacements.set(name, replacement);
            store[name] = replacement;
        };
        const originalGames = store.getRunningGames.bind(store);
        const originalPid = store.getGameForPID.bind(store);
        patch("getRunningGames", () => [...originalGames(), game]);
        patch("getGameForPID", value => value === pid ? game : originalPid(value));
        for (const name of ["getVisibleRunningGames", "getCandidateGames"]) {
            if (typeof store[name] === "function") {
                const original = store[name].bind(store);
                patch(name, () => [...original(), game]);
            }
        }
        patch("getVisibleGame", () => game);
        if (typeof store.getRunningDiscordApplicationIds === "function") {
            const original = store.getRunningDiscordApplicationIds.bind(store);
            patch("getRunningDiscordApplicationIds", () => {
                const ids = original();
                return ids instanceof Set ? new Set([...ids, row.application]) : [...(ids || []), row.application];
            });
        }
        state.modules.dispatcher.dispatch({ type: "RUNNING_GAMES_CHANGE", removed: [], added: [game], games: store.getRunningGames() });
    }
    async function game(row, context) {
        const apps = await request("get", `/applications/public?application_ids=${encodeURIComponent(row.application)}`, null, context);
        if (!apps?.[0]) throw new Error("Không tìm thấy thông tin game của Quest.");
        installGame(row, apps[0], context);
        const dispatcher = state.modules.dispatcher;
        const listener = event => {
            if (state.active !== context || context.cancelled || String(event.questId) !== row.id) return;
            readServerProgress(row, event);
        };
        dispatcher.subscribe("QUESTS_SEND_HEARTBEAT_SUCCESS", listener);
        context.cleanups.push(() => dispatcher.unsubscribe("QUESTS_SEND_HEARTBEAT_SUCCESS", listener));
        const started = Date.now();
        let lastProgress = Date.now();
        let seenProgress = row.progress;
        while (!row.completed) {
            await wait(context, 1000);
            readServerProgress(row, {});
            if (row.progress > seenProgress) { lastProgress = Date.now(); seenProgress = row.progress; }
            if (!row.completed && Date.now() - lastProgress > 120000) {
                throw new Error("Discord chưa ghi nhận game sau 2 phút. Bản Discord này có thể chưa tương thích.");
            }
            if (Date.now() - started > (row.target + 180) * 1000) throw new Error("Quest game hết thời gian chờ.");
        }
    }
    function cleanup(context) {
        for (const action of context.cleanups.splice(0).reverse()) {
            try { action(); } catch { log("Khôi phục trạng thái chưa thành công; hãy tải lại Discord.", "warning"); }
        }
    }
    async function run(context) {
        const { ids, autoClaim } = context;
        try {
            for (const [index, id] of ids.entries()) {
                check(context);
                const row = state.rows.get(id);
                if (!row?.runnable || row.claimed) continue;
                context.questId = id;
                row.status = "running";
                row.detail = "";
                log(`Quest ${index + 1}/${ids.length}: ${row.name}`);
                try {
                    if (!row.completed && !row.enrolled) {
                        const body = await request("post", `/quests/${id}/enroll`, { location: 11 }, context);
                        if (body.type && !["success", "previous_in_flight_request"].includes(body.type)) {
                            throw new Error("Discord chưa chấp nhận Quest. Hãy nhận Quest trong Discord rồi quét lại.");
                        }
                        const enrolled = camel(body.user_status || body.userStatus || body);
                        if (enrolled.enrolledAt && state.modules.dispatcher) {
                            state.modules.dispatcher.dispatch({
                                type: "QUESTS_ENROLL_SUCCESS", enrolledQuestUserStatus: enrolled
                            });
                        }
                        row.enrolled = true;
                        if (row.kind === "game" && !state.modules.quests.getQuest(id)?.userStatus?.enrolledAt) {
                            throw new Error("Quest đã nhận nhưng Discord chưa cập nhật trạng thái. Mở Quest Home rồi quét lại.");
                        }
                    }
                    if (!row.completed) {
                        if (row.kind === "video") await video(row, context);
                        else await game(row, context);
                    }
                    check(context);
                    cleanup(context);
                    row.status = "completed";
                    state.confirmed.set(`${context.owner}:${id}`, { completed: true });
                    log(`Discord đã xác nhận hoàn thành: ${row.name}`, "success");
                    if (autoClaim) {
                        try {
                            row.status = "claiming";
                            log(`Đang nhận Orbs: ${row.name}`);
                            const body = await request("post", `/quests/${id}/claim-reward`, { location: 11, platform: 4 }, context);
                            if ((body.errors && Object.keys(body.errors).length) || body.error
                                || ["error", "failure", "failed"].includes(body.type)) {
                                throw new Error("Discord chưa xác nhận nhận thưởng. Hãy kiểm tra trong Discord.");
                            }
                            row.claimed = true;
                            row.status = "claimed";
                            row.runnable = false;
                            state.confirmed.set(`${context.owner}:${id}`, { completed: true, claimed: true });
                            log(`Đã nhận thưởng: ${row.name}`, "success");
                        } catch (error) {
                            if (error.message === "ORBOT_STOPPED") throw error;
                            row.status = "claim_required";
                            row.detail = `Hoàn thành; chưa nhận được Orbs: ${error.message}`;
                            log(`${row.name}: ${row.detail}`, "warning");
                            if (error.fatal) throw error;
                        }
                    }
                } catch (error) {
                    if (error.message === "ORBOT_STOPPED") return;
                    if (!row.completed) row.status = "failed";
                    row.detail = error.message;
                    log(`${row.name}: ${error.message}`, "error");
                    if (error.fatal) {
                        state.queue.status = "blocked";
                        state.queue.error = error.message;
                        break;
                    }
                } finally { cleanup(context); }
                context.questId = null;
                if (index + 1 < ids.length) log(`Chuyển sang Quest tiếp theo (${index + 2}/${ids.length}).`);
            }
        } catch (error) {
            if (error.message !== "ORBOT_STOPPED") {
                state.queue.status = "blocked";
                state.queue.error = error.message;
                log(error.message, "error");
            }
        } finally {
            cleanup(context);
            if (state.active === context) {
                state.active = null;
                if (state.queue.status === "blocked") {
                    log(`Hàng đợi tạm dừng: ${state.queue.error} Các Quest còn chờ được giữ lại.`, "warning");
                } else {
                    state.queue.status = "finished";
                    const rows = ids.map(id => state.rows.get(id));
                    const completed = rows.filter(row => row?.completed).length;
                    const claimed = rows.filter(row => row?.claimed).length;
                    const failed = rows.filter(row => row?.status === "failed").length;
                    log(`Đã xử lý hết ${ids.length} Quest: ${completed} hoàn thành, ${claimed} đã nhận Orbs, ${failed} lỗi.`);
                }
            }
        }
    }
    function start(options) {
        if (state.active) throw new Error("Đang có hàng đợi chạy.");
        if (!ready() || accessBlocked()) throw new Error("Discord chưa sẵn sàng hoặc tài khoản đang bị hạn chế Quests.");
        refresh();
        const autoClaim = Boolean(options?.autoClaim);
        const ids = [...new Set(Array.isArray(options?.ids) ? options.ids.map(String) : [])]
            .filter(id => {
                const row = state.rows.get(id);
                return row?.runnable && !row.claimed && (autoClaim || !row.completed);
            });
        if (!ids.length) throw new Error("Chưa chọn Quest Orbs có thể chạy.");
        const context = { owner: String(currentUser().id), ids: [...ids], autoClaim,
            cancelled: false, controller: new AbortController(), cleanups: [], questId: null };
        state.queue = { runId: state.queue.runId + 1, owner: context.owner, ids: [...ids], status: "running", error: "" };
        state.active = context;
        state.lease = Date.now();
        for (const id of ids) state.rows.get(id).status = "queued";
        void run(context);
        return snapshot();
    }
    function stop() {
        const context = state.active;
        if (context) {
            context.cancelled = true;
            context.controller.abort();
            cleanup(context);
            for (const row of state.rows.values()) {
                if (row.status === "claiming") row.status = "claim_required";
                else if (["running", "queued"].includes(row.status)) row.status = "stopped";
            }
            state.active = null;
            state.queue.status = "stopped";
            log("Đã dừng và khôi phục bộ nhận diện game.");
        }
        return snapshot();
    }
    const watchdog = setInterval(() => {
        if (state.active && Date.now() - state.lease > 15000) {
            stop();
            log("Mất liên lạc với Orbot; đã dừng hàng đợi.", "warning");
        }
    }, 1000);
    globalThis.__orbot = {
        version: "0.1.3", discover, snapshot, start, stop,
        shutdown() {
            stop(); clearInterval(watchdog);
            globalThis.__orbotCapture?.dispose?.();
            delete globalThis.__orbot;
            return true;
        }
    };
})();
