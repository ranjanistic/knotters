

const postRequest = async (path, data = {}) => {
    const body = { ...data, csrfmiddlewaretoken };
    return await window.fetch(path, {
        method: "post",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
        },
        body,
    });
};
