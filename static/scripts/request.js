/**
 * Get request method with additional cache control setting params.
 * @returns {Promise<JSON|string>} response data
 */
const getRequest2 = async ({
    path,
    data = {},
    headers = {},
    options = {},
    retainCache = null,
    allowCache = null,
}) =>
    await getRequest(
        path,
        data,
        {
            ...headers,
            ...(retainCache != null && { "X-KNOT-RETAIN-CACHE": retainCache }),
            ...(allowCache != null && { "X-KNOT-ALLOW-CACHE": allowCache }),
        },
        options
    );

/**
 * Post request method with additional cache control setting params.
 * @returns {Promise<JSON|string>} response data
 */
const postRequest2 = async ({
    path,
    data = {},
    headers = {},
    options = {},
    retainCache = null,
    allowCache = null,
}) =>
    await postRequest(
        path,
        data,
        {
            ...headers,
            ...(retainCache != null && { "X-KNOT-RETAIN-CACHE": retainCache }),
            ...(allowCache != null && { "X-KNOT-ALLOW-CACHE": allowCache }),
        },
        options
    );
