const wrapper = document.getElementById('wrapper');
const loginTab = document.getElementById('login-tab');
const registerTab = document.getElementById('register-tab');
const showRegister = document.getElementById('show-register');
const showLogin = document.getElementById('show-login');

function showLoginForm() {
    wrapper.classList.remove('register-mode');
    loginTab.classList.add('active');
    registerTab.classList.remove('active');
}

function showRegisterForm() {
    wrapper.classList.add('register-mode');
    loginTab.classList.remove('active');
    registerTab.classList.add('active');
}

loginTab.addEventListener('click', showLoginForm);
registerTab.addEventListener('click', showRegisterForm);
showRegister.addEventListener('click', function(e) {
    e.preventDefault();
    showRegisterForm();
});
showLogin.addEventListener('click', function(e) {
    e.preventDefault();
    showLoginForm();
});