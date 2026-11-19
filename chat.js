const receiverId = document.getElementById("receiver-id").value;
const currentUserId = document.getElementById("messages").dataset.userId;
const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

const chatSocket = new WebSocket(
    "ws://" + window.location.host + "/ws/chat/" + receiverId + "/"
);

chatSocket.onopen = function () {
    console.log("✅ WebSocket Connected");
};

function renderBubbleHTML(data) {
    let inner = ""; 
    if (data.attachment_url) {
        if (data.attachment_type === "image") {
            inner += `<img src="${data.attachment_url}" class="mdmchat-attach-img" onclick="window.open('${data.attachment_url}')">`;
        } else if (data.attachment_type === "video") {
            inner += `<video controls src="${data.attachment_url}" class="mdmchat-attach-video"></video>`;
        } else if (data.attachment_type === "audio") {
            inner += `<audio controls src="${data.attachment_url}" class="mdmchat-attach-audio"></audio>`;
        } else {
            inner += `<a href="${data.attachment_url}" target="_blank" class="mdmchat-attach-file">📄 ${data.attachment_name || "File"}</a>`;
        }
    }
    if (data.message) {
        inner += `<div class="mdmchat-text">${data.message}</div>`;
    }
    return inner;
}

chatSocket.onmessage = function (e) {
    const data = JSON.parse(e.data);
    const messages = document.getElementById("messages");

    const isMine = String(data.sender_id) === String(currentUserId);
    const side = isMine ? "mine" : "theirs";

    messages.insertAdjacentHTML("beforeend", `
        <div class="mdmchat-row-msg ${side}">
            <div class="mdmchat-bubble">
                ${renderBubbleHTML(data)}
                <span class="mdmchat-time">${data.created_at || ""}</span>
            </div>
        </div>
    `);

    messages.scrollTop = messages.scrollHeight;

    if (!isMine) refreshBadges();
};

chatSocket.onerror = function (e) {
    console.log("❌ WebSocket Error", e);
};

chatSocket.onclose = function (e) {
    console.log("❌ WebSocket Closed", e);
};


const attachBtn = document.getElementById("attach-btn");
const fileInput = document.getElementById("file-input");
const voiceBtn = document.getElementById("voice-btn");
const preview = document.getElementById("attachment-preview");
const previewName = document.getElementById("attachment-name");
const previewCancel = document.getElementById("attachment-cancel");

let pendingFile = null;
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;


document.getElementById("send-btn").onclick = function () {
    const input = document.getElementById("message-input");

    if (pendingFile) {
        sendAttachment(input.value.trim());
        return;
    }

    if (input.value.trim() === "") return;

    chatSocket.send(JSON.stringify({ message: input.value }));
    input.value = "";
};

document.getElementById("message-input").addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
        e.preventDefault();
        document.getElementById("send-btn").click();
    }
});

attachBtn.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", () => {
    if (fileInput.files.length) {
        pendingFile = fileInput.files[0];
        previewName.textContent = pendingFile.name;
        preview.style.display = "flex";
    }
});

previewCancel.addEventListener("click", () => {
    pendingFile = null;
    fileInput.value = "";
    preview.style.display = "none";
});

voiceBtn.addEventListener("click", async () => {
    if (!isRecording) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
                pendingFile = new File([audioBlob], `voice-${Date.now()}.webm`, { type: "audio/webm" });
                previewName.textContent = "🎙️ Voice message ready";
                preview.style.display = "flex";
                stream.getTracks().forEach(track => track.stop());
            };

            mediaRecorder.start();
            isRecording = true;
            voiceBtn.classList.add("recording");
            voiceBtn.textContent = "⏹️";
        } catch (err) {
            console.error("Microphone access denied or unavailable.", err);
        }
    } else {
        mediaRecorder.stop();
        isRecording = false;
        voiceBtn.classList.remove("recording");
        voiceBtn.textContent = "🎤";
    }
});

function sendAttachment(caption) {
    const formData = new FormData();
    formData.append("attachment", pendingFile);
    formData.append("message", caption || "");

    fetch(`/chat/${receiverId}/send-attachment/`, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken },
        body: formData,
    })
    .then(res => res.json())
    .then(() => {
        pendingFile = null;
        fileInput.value = "";
        preview.style.display = "none";
        document.getElementById("message-input").value = "";
    })
    .catch(err => console.error("Attachment send failed:", err));
}

function refreshBadges() {
    fetch("/chat/unread-counts/")
        .then((r) => r.json())
        .then((counts) => {
            document.querySelectorAll(".chat-badge").forEach((el) => {
                const c = counts[el.dataset.userId] || 0;
                el.textContent = c;
                el.classList.toggle("hidden", c === 0);
            });
        });

    fetch("/messages/unread-count/")
        .then((r) => r.json())
        .then((data) => {
            const badge = document.getElementById("unread-badge");
            if (!badge) return;
            if (data.unread_count > 0) {
                badge.textContent = data.unread_count;
                badge.style.display = "inline-flex";
            } else {
                badge.style.display = "none";
            }
        });
}

refreshBadges();
setInterval(refreshBadges, 10000);

const VAPID_PUBLIC_KEY = document.getElementById("messages").dataset.vapidKey;

function urlBase64ToUint8Array(base64String) {
    const padding = "=".repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
    const rawData = atob(base64);
    return Uint8Array.from([...rawData].map(c => c.charCodeAt(0)));
}

async function subscribeUser() {
    if (!("serviceWorker" in navigator) || !("PushManager" in window)) return;

    const reg = await navigator.serviceWorker.register("/static/js/service-worker.js");
    const existing = await reg.pushManager.getSubscription();
    if (existing) return; // already subscribed

    const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY),
    });

    await fetch("/save-subscription/", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
        body: JSON.stringify(sub),
    });
}

if (Notification.permission === "granted") {
    subscribeUser();
} else if (Notification.permission !== "denied") {
    Notification.requestPermission().then(permission => {
        if (permission === "granted") subscribeUser();
    });
}