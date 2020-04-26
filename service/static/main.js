const allPages = ['Feed', 'Account'];
const allPagesNoLogin = ['Feed'];
let curPage = 'Feed';

function showErrorToast(reason) {
  $.toast({
    heading: 'Error',
    text: reason,
    showHideTransition: 'fade',
    icon: 'error',
    position: 'bottom-right'
  });
}
function showWarningToast(reason) {
  $.toast({
    heading: 'Warning',
    text: reason,
    showHideTransition: 'fade',
    icon: 'warning',
    position: 'bottom-right'
  });
}
function showInfoToast(info) {
  $.toast({
    text: info,
    showHideTransition: 'fade',
    position: 'bottom-right'
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
      updateStatusList();
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

function loadStatus(callback, error) {
  var statusContent = $('#status-content');
  $.get('/status').done(function(data) {
    if ('ok' in data) {
      callback(data['ok']);
    }
  }).fail(function(jqxhr) {
    showErrorToast(`Failed to load status: ${jqxhr.statusText}`);
    if (error !== undefined) {
      error(jqxhr.statusText);
    }
  });
}

function initDisplay() {
  $('#root').html();
  var accountPanel = $('<div>', {id: 'account-panel'});
  initAccountPanel(accountPanel);
  $('#root').append(accountPanel);
  var mainPanel = $('<div>', {id: 'main-panel'});
  initMainPanel(mainPanel);
  $('#root').append(mainPanel);
}

function initAccountPanel(panel) {
  var title = $('<div>', {class: 'title-block'});
  title.append(
    $('<span>', {class: 'title-chunk'}).text('\uD83E\uDD14'));
  title.append(
    $('<span>', {class: 'title-chunk'}).text('Deep Thoughts'));
  title.append(
    $('<span>', {class: 'title-chunk'}).text('\uD83E\uDD14'));
  panel.append(title);
  panel.append($('<div>', {class: 'main-container'}));
  panel.append($('<div>', {class: 'footer-block'}));
}

function updateNavPanel(panel, loggedIn) {
  panel.empty();
  const addNavItem = (page) => {
    const className = (page === curPage) ? 'nav-item current' : 'nav-item';
    panel.append(
      $('<div>', {class: className}).text(page)
        .click(() => {
          curPage = page;
          updateDisplay();
        }));
  };
  if (loggedIn) {
    allPages.forEach(addNavItem);
  }
  else {
    allPagesNoLogin.forEach(addNavItem);
  }
}

function initMainPanel(panel) {
  panel.append($('<div>', {id: 'nav-panel'}));
  panel.append($('<div>', {id: 'content-panel'}));
}

function updateDisplay() {
  var loggedIn = (!!Cookies.get('session_id')) && (!!Cookies.get('username'));
  var username = Cookies.get('username');
  updateAccountPanel(loggedIn, username);
  updateMainPanel(loggedIn, username);
}

function makeTextInput(name, id) {
  return $('<input>', {class: 'input-block', type: 'text', autocomplete: 'off', name, id});
}

function updateAccountPanel(loggedIn, username) {
  const panelContent = $('#account-panel .main-container');
  const panelFooter = $('#account-panel .footer-block');
  panelContent.empty();
  panelFooter.empty();
  if (!loggedIn) {
    const loginBox = $('<div>', {class: 'account-box'});
    loginBox.append($('<div>', {class: 'account-header'}).text('Log in'));
    const loginForm = $('<form>', {class: 'boxed-form'}).submit(login);
    loginForm.append($('<label>', {for: 'login_username'}).text('Username'));
    loginForm.append(makeTextInput('username', 'login_username'));
    loginForm.append($('<label>', {for: 'login_password'}).text('Password'));
    loginForm.append($('<input>', {class: 'input-block', type: 'password', name: 'password', id: 'login_password'}));
    loginForm.append($('<input>', {class: 'button-block button', type: 'submit', value: 'Login'}));
    loginBox.append(loginForm);
    panelContent.append(loginBox);
    const registerBox = $('<div>', {class: 'account-box'});
    registerBox.append($('<div>', {class: 'account-header'}).text('Register'));
    const registerForm = $('<form>', {class: 'boxed-form'}).submit(register);
    registerForm.append($('<label>', {for: 'register_username'}).text('Username'));
    registerForm.append(makeTextInput('username', 'register_username'));
    registerForm.append($('<label>', {for: 'register_password'}).text('Password'));
    registerForm.append($('<input>', {class: 'input-block', type: 'password', name: 'password', id: 'register_password'}));
    registerForm.append($('<input>', {class: 'button-block button', type: 'submit', value: 'Register'}));
    registerBox.append(registerForm);
    panelContent.append(registerBox);
  }
  else {
    const accountBox = $('<div>', {class: 'account-box'});
    accountBox.append($('<div>', {class: 'account-header'}).text(`Welcome, ${username}`));
    const statusForm = $('<form>', {id: 'set-status', class: 'boxed-form'}).submit(setStatus);
    statusForm.append($('<label>', {for: 'status_field'}).text('What is your deep mood?'));
    const statusField = makeTextInput('status', 'status_field');
    statusForm.append(statusField);
    statusForm.append($('<input>', {class: 'button-block button', type: 'submit', value: 'Update mood'}));
    loadStatus((status) => {
      statusField.attr('placeholder', status);
    });
    accountBox.append(statusForm);
    panelContent.append(accountBox);
    const logoutBox = $('<div>', {class: 'account-box footer'});
    const logoutForm = $('<form>', {}).submit(logout);
    logoutForm.append($('<input>', {class: 'button-block button', type: 'submit', value: 'Log out'}));
    logoutBox.append(logoutForm);
    panelFooter.append(logoutBox);
  }
}

function renderTable(objects, keys, prettyKeys) {
  const table = $('<table>');
  const thead = $('<thead>');
  const theadRow = $('<tr>');
  prettyKeys.forEach((key) => {
    theadRow.append($('<th>').text(key));
  });
  thead.append(theadRow);
  table.append(thead);
  const tbody = $('<tbody>');
  objects.forEach((obj) => {
    const tbodyRow = $('<tr>');
    keys.forEach((key, i) => {
      tbodyRow.append($('<td>').text(obj[key]));
    });
    tbody.append(tbodyRow);
  });
  table.append(tbody);
  return table;
}

function renderFeed(container) {
  container.text('Loading...');
  const reqBroadcast = $.get('/broadcast_messages');
  const reqMessages = $.get('/messages');
  $.when(reqBroadcast, reqMessages)
    .done(function(data1, data2) {
      const allMsg = data1.concat(data2);
      allMsg.sort((a,b) => (b.timestamp - a.timestamp));
      container.empty();
      container.append($('<h3>').text('Latest messages'));
      container.append(renderTable(
        allMsg, ['author', 'message', 'recipients', 'timestamp', 'encrypted'],
        ['Author', 'Message', 'To', 'Time', 'Encrypted?']));
    })
    .fail(function() {
      container.text('<Failed to load>');
      showErrorToast('Failed to load messages');
    });
}

function renderPublicKey(keyData) {
  const key = keyData.ok;
  const content = $('<div>', {class: 'rsakey public'});
  if (key !== undefined) {
    const keyN = new BigInteger(key.n, 16);
    content.append($('<p>').text('n = ' + keyN.toString(16)));
  }
  else {
    content.append($('<p>').text('<Failed to load>'));
  }
  return content;
}
function renderPrivateKey(keyData) {
  const key = keyData.ok;
  const content = $('<div>', {class: 'rsakey private'});
  if (key !== undefined) {
    const keyN = new BigInteger(key.n, 16);
    const keyD = new BigInteger(key.d, 16);
    content.append($('<p>').text('n = ' + keyN.toString(16)));
    content.append($('<p>').text('d = ' + keyD.toString(16)));
  }
  else {
    content.append($('<p>').text('<Failed to load>'));
  }
  return content;
}

function renderAccount(container, username) {
  const reqPubKey = $.get(`/pub_key?username=${username}`);
  const reqPrivKey = $.get('/priv_key');
  const keysContent = $('<div>', {class: 'content-block'});
  keysContent.text('Loading...');
  container.empty();
  container.append(keysContent);
  $.when(reqPubKey, reqPrivKey)
    .done(function([pubData], [privData]) {
      console.log(pubData, privData);
      if ('error' in pubData) {
        showErrorToast(pubData['error']);
      }
      if ('error' in privData) {
        showErrorToast(privData['error']);
      }
      keysContent.empty();
      keysContent.append($('<h3>').text('Your public key'));
      keysContent.append(renderPublicKey(pubData));
      keysContent.append($('<h3>').text('Your private key'));
      keysContent.append(renderPrivateKey(privData));
    })
    .fail(function() {
      keysContent.text('<Failed to load>');
      showErrorToast('Failed to load keys');
    });
}

function updateMainPanel(loggedIn, username) {
  const navPanel = $('#nav-panel');
  updateNavPanel(navPanel, loggedIn);
  const availablePages = loggedIn ? allPages : allPagesNoLogin;
  if (availablePages.indexOf(curPage) < 0) {
    curPage = availablePages[0];
  }
  const content = $('#content-panel');
  if (curPage === 'Feed') {
    renderFeed(content);
  }
  else if (curPage === 'Account') {
    renderAccount(content, username);
  }
}

// function updateStatusList() {
//   var statusList = $('#status-list');
//   statusList.text('Loading...');
//   $.get('/status_all')
//     .done(function(data) {
//       if ('error' in data) {
//         showErrorToast(data['error']);
//         statusList.text('<Failed to load>');
//       }
//       else if (!('ok' in data)) {
//         statusList.text('<Failed to load>');
//       }
//       else {
//         statusList.html('<table>');
//         var statusTable = $('#status-list table');
//         $.each(data['ok'], function(i, item) {
//           var tr = $('<tr>').append(
//             $('<td>').text(item.username),
//             $('<td>').text(item.status)
//           ).appendTo(statusTable);
//         });
//       }
//     })
//     .fail(function(jqxhr) {
//       statusList.text('<Failed to load>');
//     });
// }

$(document).ready(function() {
  initDisplay();
  updateDisplay();
});
