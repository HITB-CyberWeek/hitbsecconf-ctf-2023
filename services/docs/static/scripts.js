const baseUrl = "";
var createDocumentModal = document.getElementById("createDocumentModal");
var createDocumentModalObject = new Modal(createDocumentModal);

async function postJsonRequest(url, data) {
    return await fetch(`${baseUrl}${url}`, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(data), credentials: 'include'});
}

function showToast(id) {
    const toast = document.getElementById(id);
    toast.classList.remove("hidden");
    setTimeout(() => {toast.classList.add("hidden")}, 1000);
}

async function processLogin() {
    const login = document.getElementById("loginForm_login").value;
    const password = document.getElementById("loginForm_password").value;
    let r;
    try {
        r = await postJsonRequest("/login", {login, password});
    } catch (e) {
        console.log(e);
        showToast("wrongPasswordToast");
        return false;
    }
    if (r.status != 204) {
        showToast("wrongPasswordToast");
        return false;
    }
    await loadDocuments();
    return false;
}

async function processRegistration() {
    const login = document.getElementById("registrationForm_login").value;
    const password = document.getElementById("registrationForm_password").value;
    const org = document.getElementById("registrationForm_org").value;
    let r;
    try {
        r = await postJsonRequest("/register", {login, password, org});
    } catch (e) {
        console.error(e);
        showToast("wrongRegistrationToast");
        return false;
    }
    if (r.status != 200) {
        showToast("wrongRegistrationToast");
        return false;
    }

    showLogin();
    return false;
}

async function loadDocuments() {
    const createDocumentButton = document.getElementById("createDocumentButton");
    const documentsList = document.getElementById("documentsList");
    const tbody = documentsList.getElementsByTagName("tbody")[0];
    const row = tbody.getElementsByTagName("tr")[0];
    Array.from(tbody.getElementsByTagName("tr")).slice(1).forEach(n => n.remove());

    const r = await fetch(`${baseUrl}/docs`);
    const json = await r.json();
    createDocumentButton.classList.remove("hidden");
    json.docs.forEach(d => {
        const documentRow = row.cloneNode(true);
        documentRow.classList.remove("hidden");
        documentRow.getElementsByTagName("th")[0].innerText = d.title;
        documentRow.getElementsByTagName("td")[0].innerText = d.owner_login;
        documentRow.getElementsByTagName("td")[1].innerText = d.created;
        let sharedWith = d.shares_logins;
        if (sharedWith && sharedWith.startsWith("{"))
            sharedWith = sharedWith.substring(1, sharedWith.length - 1).replaceAll(",", ", ");
        documentRow.getElementsByTagName("td")[2].innerText = sharedWith;
        documentRow.onclick = async function() { await showDocument(d.id, d.title) };
        tbody.appendChild(documentRow);
    });
    showDocuments();
}

async function showDocument(documentId, documentTitle) {
    const documentModal = document.getElementById("documentModal");

    const r = await fetch(`${baseUrl}/contents/${documentId}`);
    let documentContent;
    if (r.status == 403) {
        documentContent = "You don't have permission to view this document"
    } else {
        documentContent = await r.text();
    }

    document.getElementById("documentModal_title").innerText = documentTitle;
    document.getElementById("documentModal_content").innerText = documentContent;

    const modal = new Modal(documentModal);
    Array.from(documentModal.getElementsByTagName("button")).forEach(b => {
        b.addEventListener('click', () => {
            modal.hide();
        });
    });
    modal.show();
}

async function openCreateDocumentModal() {
    const createDocumentModal_share = document.getElementById("createDocumentModal_share");

    createDocumentModal_share.innerHTML = "";

    const r = await fetch(`${baseUrl}/users`);
    const users = await r.json();
    users.users.forEach(u => {
        const option = document.createElement("option");
        option.value = u.id;
        option.innerText = `${u.login}@${u.org}`;
        createDocumentModal_share.appendChild(option);
    });

    Array.from(createDocumentModal.getElementsByTagName("button")).forEach(b => {
        if (b.type === "button") {
            b.addEventListener('click', () => {
                createDocumentModalObject.hide();
            });
        }
    });
    createDocumentModalObject.show();
}

function getSelectValues(select) {
    var result = [];
    var options = select && select.options;
    var opt;

    for (var i=0, iLen=options.length; i<iLen; i++) {
      opt = options[i];

      if (opt.selected) {
        result.push(opt.value || opt.text);
      }
    }
    return result;
  }

async function createDocument() {
    const title = document.getElementById("createDocumentModal_title").value;
    const data = document.getElementById("createDocumentModal_content").value;
    const createDocumentModal_share = document.getElementById("createDocumentModal_share");
    const shares = getSelectValues(createDocumentModal_share);

    const r = await postJsonRequest("/docs", {title, shares});
    const response = await r.json();
    const documentId = response.id;

    await postJsonRequest("/contents", {doc_id: documentId, data});
    createDocumentModalObject.hide();
    await loadDocuments();
}

function hideAllExceptOne(except) {
    const all = ["loginForm", "registrationForm", "documentsList"];
    all.forEach(x => document.getElementById(x).classList.add("hidden"));
    document.getElementById(except).classList.remove("hidden");
    return false;
}

const showLogin = () => hideAllExceptOne("loginForm");
const showRegistration = () => hideAllExceptOne("registrationForm");
const showDocuments = () => hideAllExceptOne("documentsList");

async function autoLogin() {
    const r = await fetch(`${baseUrl}/users`);
    if (r.status == 200) {
        await loadDocuments();
    }
}


autoLogin().catch(console.error);
