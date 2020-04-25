function showErrorToast(reason) {
  $.toast({
    heading: 'Error',
    text: reason,
    showHideTransition: 'fade',
    icon: 'error'
  });
}
function showWarningToast(reason) {
  $.toast({
    heading: 'Warning',
    text: reason,
    showHideTransition: 'fade',
    icon: 'warning'
  });
}
function showInfoToast(info) {
  $.toast({
    text: info,
    showHideTransition: 'fade'
  });
}

function login(event) {
  event.preventDefault();
  var formData = new FormData(event.target);
  formData.append('handshake', Math.random().toString(36).substring(2,15));
  $.ajax('/login', {
    method: 'POST',
    processData: false,
    contentType: false,
    data: formData
  }).done(function(data) {
    if ('error' in data) {
      showErrorToast(data['error']);
    }
    else if (!('ok' in data)) {
      showWarningToast('Login failed for unknown reason');
    }
    else {
      showInfoToast('Login success');
      updateDisplay();
    }
  });
}

function register(event) {
  event.preventDefault();
  var formData = new FormData(event.target);
  formData.append('handshake', Math.random().toString(36).substring(2,15));
  $.ajax('/register', {
    method: 'POST',
    processData: false,
    contentType: false,
    data: formData
  }).done(function(data) {
    if ('error' in data) {
      showErrorToast(data['error']);
    }
    else if (!('ok' in data)) {
      showWarningToast('Register failed for unknown reason');
    }
    else {
      showInfoToast('Register success');
      updateDisplay();
    }
  });
}

function setStatus(event) {
  event.preventDefault();
  var formData = new FormData(event.target);
  $.ajax('/set_status', {
    method: 'POST',
    processData: false,
    contentType: false,
    data: formData
  }).done(function(data) {
    if ('error' in data) {
      showErrorToast(data['error']);
    }
    else if (!('ok' in data)) {
      showWarningToast('Set status failed for unknown reason');
    }
    else {
      showInfoToast('Status updated');
      updateDisplay();
    }
  });
}

function updateDisplay() {
  var loginForm = $('#login');
  var registerForm = $('#register');
  var statusForm = $('#set-status');
  var greeting = $('#greeting');
  var status = $('#status');
  var statusContent = $('#status-content');
  var loggedIn = (!!Cookies.get('session_id')) && (!!Cookies.get('username'));
  var username = Cookies.get('username');
  if (loggedIn) {
    loginForm.css('display', 'none');
    registerForm.css('display', 'none');
    statusForm.css('display', '');
    status.css('display', '');
    greeting.text(`Hello ${username}!`);
    statusContent.text('Loading...');
    $.get('/status').done(function(data) {
      if ('ok' in data) {
        statusContent.text(data['ok']);
      }
    });
  }
  else {
    loginForm.css('display', '');
    registerForm.css('display', '');
    statusForm.css('display', 'none');
    status.css('display', 'none');
    greeting.text('Welcome. Please log in!');
    statusContent.text('');
  }
}

$(document).ready(function() {
  var loginForm = $('#login');
  var registerForm = $('#register');
  var statusForm = $('#set-status');
  loginForm.submit(login);
  registerForm.submit(register);
  statusForm.submit(setStatus);
  updateDisplay();
});
