const allPages = ['Feed', 'Account'];
const allPagesNoLogin = ['Feed'];
let curPage = 'Feed';
let rsaKey;
let keyRetryTimer;

function loadKeys(username) {
  const reqPubKey = $.get(`/pub_key?username=${username}`);
  const reqPrivKey = $.get('/priv_key');
  $.when(reqPubKey, reqPrivKey)
    .done(function([pubData], [privData]) {
      if ('error' in pubData) {
        showErrorToast(`Failed to load keys (${pubData['error']}), retrying in 30s`);
        setTimeout(loadKeys, 30*1000);
        keyRetryTimer = Date.now() + 30*1000;
        return;
      }
      if ('error' in privData) {
        showErrorToast(`Failed to load keys (${privData['error']}), retrying in 30s`);
        setTimeout(loadKeys, 30*1000);
        return;
      }
      const {n: nPub} = pubData.ok;
      const {n: nPriv, d: dPriv} = privData.ok;
      if (nPub !== nPriv) {
        showErrorToast(`Failed to load keys (pub/priv mismatch), retrying in 30s`);
        setTimeout(loadKeys, 30*1000);
        keyRetryTimer = Date.now() + 30*1000;
        return;
      }
      keyRetryTimer = undefined;
      rsaKey = {n: nPriv, d: dPriv};
    })
    .fail(function() {
      showErrorToast(`Failed to load keys, retrying in 30s`);
      setTimeout(loadKeys, 30*1000);
      keyRetryTimer = Date.now() + 30*1000;
    });
}

function isLoggedIn() {
  return (!!Cookies.get('session_id')) && (!!Cookies.get('username'));
}

function initState() {
  const username = Cookies.get('username');
  if (isLoggedIn()) {
    loadKeys(username);
  }
}

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
  const formData = new FormData(event.target);
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
      loadKeys(Cookies.get('username'));
      updateDisplay();
    }
  }).fail(function(jqxhr) {
    showErrorToast(`${jqxhr.statusText}`);
  });
}

function register(event) {
  event.preventDefault();
  const formData = new FormData(event.target);
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
      loadKeys(Cookies.get('username'));
      updateDisplay();
    }
  }).fail(function(jqxhr) {
    showErrorToast(`${jqxhr.statusText}`);
  });
}

function setStatus(event) {
  event.preventDefault();
  const formData = new FormData(event.target);
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

function randomBytes(n) {
  return Array.from(Array(n), () => Math.floor(256*Math.random()));
}
function padBytes(bytes) {
  const pad = (16 - bytes.length % 16);
  const padArr = Array(pad).fill(pad);
  const padded = new Uint8Array(bytes.length + pad);
  padded.set(bytes);
  padded.fill(pad, bytes.length);
  return padded;
}
function unpadBytes(bytes) {
  const pad = bytes[bytes.length-1];
  if (pad > 16) { // something wrong
    return bytes;
  }
  else {
    return bytes.slice(0, bytes.length-pad);
  }
}
function expMod(base, exp, mod) {
  if (exp == 0) return 1n;
  if (exp % 2n == 0) {
    return (expMod(base, (exp/2n), mod) ** 2n) % mod;
  }
  else {
    return (base * expMod(base, (exp-1n), mod)) % mod;
  }
}
// function rsaEncrypt(pubKey, bytes) {
//   const m = BigInt('0x' + aesjs.utils.hex.fromBytes(bytes));
//   const n = BigInt('0x' + pubKey.n);
//   const e = 3n;
//   let out = expMod(m, e, n).toString(16);
//   if (out.length % 2 != 0) {
//     out = '0' + out;
//   }
//   return aesjs.utils.hex.toBytes(out);
// }
function rsaDecrypt(privKey, crypt) {
  const mp = BigInt('0x' + aesjs.utils.hex.fromBytes(crypt));
  console.log('mp =', mp);
  const n = BigInt('0x' + privKey.n);
  const d = BigInt('0x' + privKey.d);
  console.log('n =', n);
  console.log('d =', d);
  let out = expMod(mp, d, n).toString(16);
  out = '0'.repeat(256 - out.length) + out;
  return aesjs.utils.hex.toBytes(out);
}

function postMessage(event) {
  event.preventDefault();
  if (!isLoggedIn()) {
    showErrorToast('You must login to post a message');
    return;
  }
  if (rsaKey === undefined) {
    const retryTimeLeft = (keyRetryTimer - Date.now()) / 1000;
    showErrorToast(`Your keys are not loaded, wait for retry (${retryTimeLeft} s)`);
    return;
  }
  const formData = new FormData(event.target);
  const message = formData.get('message');
  let messageBytes = aesjs.utils.utf8.toBytes(message);
  const encrypted = !!(formData.get('encrypt'));
  formData.delete('encrypt');
  const recipients = [];
  if (formData.get('share_1') !== undefined &&
      formData.get('share_1') !== '') {
    recipients.push(formData.get('share_1'));
  }
  formData.delete('share_1');
  if (formData.get('share_2') !== undefined &&
      formData.get('share_2') !== '') {
    recipients.push(formData.get('share_2'));
  }
  formData.delete('share_2');
  const messageObj = {
    'encrypted': encrypted,
    'message': aesjs.utils.hex.fromBytes(messageBytes)
  };
  if (recipients.length > 0) {
    messageObj['recipients'] = recipients;
  }
  formData.set('message', JSON.stringify(messageObj));
  $.ajax('/post_message', {
    method: 'POST',
    processData: false,
    contentType: false,
    data: formData
  }).done(function(data) {
    if ('error' in data) {
      showErrorToast(data['error']);
    }
    else if (!('ok' in data)) {
      showWarningToast('Post message failed for unknown reason');
    }
    else {
      showInfoToast('Message published');
      // TODO: update display?
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
  rsaKey = undefined;
  updateDisplay();
}

function loadStatus(callback, error) {
  const statusContent = $('#status-content');
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
  const accountPanel = $('<div>', {id: 'account-panel'});
  initAccountPanel(accountPanel);
  $('#root').append(accountPanel);
  const mainPanel = $('<div>', {id: 'main-panel'});
  initMainPanel(mainPanel);
  $('#root').append(mainPanel);
}

function initAccountPanel(panel) {
  const title = $('<div>', {class: 'title-block'});
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
  const loggedIn = isLoggedIn();
  const username = Cookies.get('username');
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
    const logoutBox = $('<div>', {class: 'account-box'});
    const logoutForm = $('<form>', {}).submit(logout);
    logoutForm.append($('<input>', {class: 'button-block button', type: 'submit', value: 'Log out'}));
    logoutBox.append(logoutForm);
    panelFooter.append(logoutBox);
  }
}

function eventuallyDecryptMessage(message, numRecipients, td) {
  if (rsaKey === undefined) {
    console.log('No RSA key yet, delaying decryption');
    setTimeout(() => eventuallyDecryptMessage(message, td), 1000);
    return;
  }
  const numKeys = numRecipients + 1; // one for author
  const iv = message.slice(128*numKeys, 128*numKeys+16);
  const encrypted = message.slice(128*numKeys + 16, message.length);
  for (const i of Array(numKeys).keys()) {
    console.log(`Try ${i}`);
    const encryptedKey = message.slice(128*i, 128*(i+1));
    console.log('Enc key =', aesjs.utils.hex.fromBytes(encryptedKey));
    const keyPad = rsaDecrypt(rsaKey, encryptedKey);
    console.log('key pad whole', aesjs.utils.hex.fromBytes(keyPad));
    console.log(aesjs.utils.hex.fromBytes(keyPad.slice(32, 48)),
                aesjs.utils.hex.fromBytes(keyPad.slice(48, 64)));
    if (aesjs.utils.hex.fromBytes(keyPad.slice(32, 48)) ==
        aesjs.utils.hex.fromBytes(keyPad.slice(48, 64))
        || i === numKeys-1) {
      const key = keyPad.slice(32, 48);
      const aesCbc = new aesjs.ModeOfOperation.cbc(key, iv);
      message = unpadBytes(aesCbc.decrypt(encrypted));
      td.text(aesjs.utils.utf8.fromBytes(message)).removeClass('info');
      return;
    }
  }
}

function renderMessageTd(hexMsg, isEncrypted, numRecipients) {
  let message = aesjs.utils.hex.toBytes(hexMsg);
  const td = $('<td>');
  if (isEncrypted) {
    if (isLoggedIn()) {
      setTimeout(() => eventuallyDecryptMessage(message, numRecipients, td), 500);
      td.text('Loading...').addClass('info');
    }
    else {
      td.text('Login to decrypt...').addClass('info');
    }
  }
  else {
    const outMessage = aesjs.utils.utf8.fromBytes(message);
    td.text(outMessage).removeClass('info');
  }
  return td;
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
    if (obj.message === undefined) {
      return;
    }
    // let message = aesjs.utils.hex.toBytes(obj.message);
    // obj.message = aesjs.utils.utf8.fromBytes(message);
    const tbodyRow = $('<tr>');
    keys.forEach((key, i) => {
      if (key === 'message') {
        if (obj.recipients !== undefined) {
          tbodyRow.append(renderMessageTd(obj[key], obj.encrypted, obj.recipients.length));
        }
        else {
          tbodyRow.append(renderMessageTd(obj[key], obj.encrypted, 0));
        }
      }
      else if (key === 'timestamp') {
        const date = new Date(obj[key]*1000);
        tbodyRow.append($('<td>').text(date.toLocaleString()));
      }
      else {
        tbodyRow.append($('<td>').text(obj[key]));
      }
    });
    tbody.append(tbodyRow);
  });
  table.append(tbody);
  return table;
}

function renderMessages(container) {
  container.text('Loading...');
  const reqBroadcast = $.get('/broadcast_messages');
  const reqMessages = $.get('/messages');
  $.when(reqBroadcast, reqMessages)
    .done(function([{ok: data1}], [{ok: data2}]) {
      let allMsg = [];
      if (data1 !== undefined) {
        allMsg = allMsg.concat(data1);
      }
      if (data2 !== undefined) {
        allMsg = allMsg.concat(data2);
      }
      allMsg = allMsg.filter(msg => (msg.timestamp !== undefined));
      allMsg.sort((a,b) => (b.timestamp - a.timestamp));
      container.empty();
      container.append($('<h3>').text('Latest thoughts'));
      container.append(renderTable(
        allMsg, ['author', 'message', 'recipients', 'timestamp', 'encrypted'],
        ['Author', 'Message', 'To', 'Time', 'Encrypted?']));
    })
    .fail(function() {
      container.text('<Failed to load>');
      showErrorToast('Failed to load messages');
    });
}

function renderFeed(container) {
  const writeContainer = $('<div>');
  const writeForm = $('<form>', {class: 'message_form'}).submit(postMessage);
  const writeFormHeader = $('<div>', {class: 'textarea_header'});
  writeFormHeader.append($('<label>', {for: 'message_field'}).html('<h3>Enter your Deep Thought</h3>'));
  const writeFormHeaderShare = $('<div>', {class: 'share_with hidden'});
  writeFormHeaderShare.append($('<label>').text('Share with:'));
  writeFormHeaderShare.append($('<input>', {id: 'message_share_1', type: 'text', name: 'share_1'}));
  writeFormHeaderShare.append($('<input>', {id: 'message_share_2', type: 'text', name: 'share_2'}));
  writeFormHeader.append(writeFormHeaderShare);
  writeForm.append(writeFormHeader);
  writeForm.append($('<textarea>', {id: 'message_field', name: 'message'}));
  const writeFormFiddlyBits = $('<div>', {class: 'fiddly_bits'});
  writeFormFiddlyBits.append(
    $('<span>', {class: 'message_details'})
      .text('Private messages are always doubly encrypted using the most modern cipher '
            + 'and public key technology. Of course they are visible so fans know '
            + 'you had a Deep Thought!'));
  const writeFormFiddlyBitsGroup = $('<span>', {class: 'fiddly_bits_group'});
  writeFormFiddlyBitsGroup.append(
    $('<input>', {id: 'message_encrypt', type: 'checkbox', name: 'encrypt'})
      .change(function() {
        if ($(this).is(':checked')) {
          writeFormHeaderShare.removeClass('hidden');
        }
        else {
          writeFormHeaderShare.addClass('hidden');
        }
      }));
  writeFormFiddlyBitsGroup.append($('<label>', {for: 'message_encrypt'}).text('Make private'));
  writeFormFiddlyBitsGroup.append($('<input>', {class: 'button', type: 'submit', value: 'Publish'}));
  writeFormFiddlyBits.append(writeFormFiddlyBitsGroup);
  writeForm.append(writeFormFiddlyBits);
  writeContainer.append(writeForm);
  if (isLoggedIn()) {
    container.append(writeContainer);
  }
  const messageContainer = $('<div>');
  renderMessages(messageContainer);
  container.append(messageContainer);
}

function renderPublicKey(keyData) {
  const key = keyData.ok;
  const content = $('<div>', {class: 'rsakey public'});
  if (key !== undefined) {
    const keyN = BigInt('0x' + key.n);
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
    const keyN = BigInt('0x' + key.n);
    const keyD = BigInt('0x' + key.d);
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
  content.empty();
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
  initState();
  initDisplay();
  updateDisplay();
});
