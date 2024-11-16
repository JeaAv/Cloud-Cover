let auth0Client;

// Initialize Auth0 client
const initializeAuth0 = async () => {
    auth0Client = await createAuth0Client({
        domain: "dev-txal0zdxum5np65h.us.auth0.com",
        client_id: "wJrsVXMV1XZjiiUGfanHjyU6oPYvhOpn",
        redirect_uri: window.location.origin + "/callback" // Specify the callback URL after login
    });
};

// Handle login with Auth0
const login = async () => {
    await auth0Client.loginWithRedirect({
        redirect_uri: window.location.origin + "/callback"
    });
};

// Check if redirected after login
const handleRedirectCallback = async () => {
    const result = await auth0Client.handleRedirectCallback();
    console.log(result);
    window.location.replace('/'); // Redirect to home after successful login
};

// Check if the user is authenticated
const updateUI = async () => {
    const user = await auth0Client.getUser();
    const authButton = document.getElementById('authLoginButton');

    if (user) {
        // Logged in user: change UI (you can show user info here)
        authButton.innerText = 'Logged In';
    } else {
        // Not logged in: show login button
        authButton.innerText = 'Log in with Auth0';
    }
};

// Set up Auth0 login button
window.addEventListener('DOMContentLoaded', async () => {
    await initializeAuth0();

    // Check if the user was redirected back after login
    if (window.location.search.includes("code=") && window.location.search.includes("state=")) {
        await handleRedirectCallback();
    } else {
        await updateUI();
    }

    // Handle Auth0 login button click
    const authLoginButton = document.getElementById('authLoginButton');
    if (authLoginButton) {
        authLoginButton.addEventListener('click', login);
    }
});
