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
  }).fail(function(jqxhr) {
    showErrorToast(`${jqxhr.statusText}`);
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
  }).fail(function(jqxhr) {
    showErrorToast(`${jqxhr.statusText}`);
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
  }).fail(function(jqxhr) {
    showErrorToast(`${jqxhr.statusText}`);
  });
}

function logout(event) {
  Cookies.remove('username');
  Cookies.remove('session_id');
  Cookies.remove('session_handshake');
  updateDisplay();
}

function loadStatus() {
  var statusContent = $('#status-content');
  $.get('/status').done(function(data) {
    if ('ok' in data) {
      statusContent.text(data['ok']);
    }
  }).fail(function(jqxhr) {
    statusContent.text('<Failed to load>');
    showErrorToast(`Failed to load status: ${jqxhr.statusText}`);
  });
}

function updateDisplay() {
  var greeting = $('#greeting');
  var statusContent = $('#status-content');
  var loggedIn = (!!Cookies.get('session_id')) && (!!Cookies.get('username'));
  var username = Cookies.get('username');
  if (loggedIn) {
    $('.if-logged-in').css('display', '');
    $('.if-not-logged-in').css('display', 'none');
    greeting.text(`Hello ${username}!`);
    statusContent.text('Loading...');
    loadStatus();
  }
  else {
    $('.if-logged-in').css('display', 'none');
    $('.if-not-logged-in').css('display', '');
    greeting.text('Welcome. Please log in!');
    statusContent.text('');
  }
}

$(document).ready(function() {
  var loginForm = $('#login');
  var registerForm = $('#register');
  var statusForm = $('#set-status');
  var logoutForm = $('#logout');
  loginForm.submit(login);
  registerForm.submit(register);
  statusForm.submit(setStatus);
  logoutForm.submit(logout);
  updateDisplay();
});
