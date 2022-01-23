/**
 * Get request method with additional cache control setting params.
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
 * Post request method with additional cache control setting params.
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
