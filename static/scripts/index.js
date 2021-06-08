

const postRequest = async (path, data = {}) => {
    const body = { ...data};
    response = await window.fetch(path, {
        method: "post",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": csrfmiddlewaretoken
        },
        body,
    });
    return response;
};
