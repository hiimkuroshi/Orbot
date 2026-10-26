/* Capture module exports during a user-requested renderer reload. No credentials are read. */
(() => {
    "use strict";
    if (globalThis.__orbotCapture) return;
    const modules = new Set();
    const loaders = new Set();
    const wrapped = new WeakMap();
    const records = [];
    let enabled = true;
    let chunkArray;
    const wrapChunk = chunk => {
        if (!enabled) return;
        const factories = chunk?.[1];
        if (!factories || typeof factories !== "object") return;
        for (const key of Object.keys(factories)) {
            const factory = factories[key];
            if (typeof factory !== "function" || wrapped.has(factory)) continue;
            const replacement = function (module, exports, require) {
                if (enabled && require) loaders.add(require);
                const result = factory.apply(this, arguments);
                if (enabled && module?.exports) modules.add(module.exports);
                return result;
            };
            replacement.toString = factory.toString.bind(factory);
            wrapped.set(replacement, factory);
            factories[key] = replacement;
            records.push({ factories, key, factory, replacement });
        }
    };
    const attach = array => {
        if (!Array.isArray(array)) return;
        array.forEach(wrapChunk);
        let push = array.push;
        Object.defineProperty(array, "push", {
            configurable: true,
            get() {
                const handler = push;
                return function (...chunks) {
                    chunks.forEach(wrapChunk);
                    return handler.apply(this, chunks);
                };
            },
            set(value) { push = value; }
        });
    };
    chunkArray = globalThis.webpackChunkdiscord_app;
    if (chunkArray) attach(chunkArray);
    Object.defineProperty(globalThis, "webpackChunkdiscord_app", {
        configurable: true,
        get: () => chunkArray,
        set(value) {
            if (value !== chunkArray) { chunkArray = value; attach(value); }
        }
    });
    globalThis.__orbotCapture = {
        modules, loaders,
        dispose() {
            enabled = false;
            for (const record of records) {
                if (record.factories[record.key] === record.replacement) record.factories[record.key] = record.factory;
            }
            modules.clear(); loaders.clear(); records.length = 0;
            delete globalThis.__orbotCapture;
        }
    };
})();
