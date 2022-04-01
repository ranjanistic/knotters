/**
 * GET request method with additional request control setting params.
 * @param {string} path - request path
 * @param {Object} data - request data
 * @param {Object} headers - request headers
 * @param {Object} options - request options
 * @param {boolean} retainCache - retain existing dynamic caches (by default, no GET requests affect existing dynamic caches)
 * @param {boolean} allowCache - allow dynamic caching (by default, all GET requests are cached dynamically)
 * @param {boolean} silent - silent mode (no loaders, no errors)
 * @returns {Promise<JSON|string|boolean>} response data
 */
const getRequest2 = async ({
    path,
    data = {},
    headers = {},
    options = {},
    retainCache = null,
    allowCache = null,
    silent = false,
}) =>
    await getRequest(
        path,
        data,
        {
            ...headers,
            ...(retainCache != null && { "X-KNOT-RETAIN-CACHE": retainCache }),
            ...(allowCache != null && { "X-KNOT-ALLOW-CACHE": allowCache }),
        },
        options,
        silent
    );

/**
 * POST request method with additional request control setting params.
 * @param {string} path - request path
 * @param {Object} data - request data
 * @param {Object} headers - request headers
 * @param {Object} options - request options
 * @param {boolean} retainCache - retain existing dynamic caches (by default, all POST requests clear existing dynamic caches)
 * @param {boolean} allowCache - allow dynamic caching (by default, no POST requests are cached dynamically)
 * @param {boolean} silent - silent mode (no loaders, no errors)
 * @returns {Promise<JSON|string|boolean>} response data
 */
const postRequest2 = async ({
    path,
    data = {},
    headers = {},
    options = {},
    retainCache = null,
    allowCache = null,
    silent = false,
}) =>
    await postRequest(
        path,
        data,
        {
            ...headers,
            ...(retainCache != null && { "X-KNOT-RETAIN-CACHE": retainCache }),
            ...(allowCache != null && { "X-KNOT-ALLOW-CACHE": allowCache }),
        },
        options,
        silent
    );
