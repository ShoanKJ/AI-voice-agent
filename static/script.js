document.addEventListener("DOMContentLoaded", () => {
    const startBtn = document.getElementById("startBtn");
    const stopBtn = document.getElementById("stopBtn");
    const statusMsg = document.getElementById("status");
    let mediaRecorder;
    let audioChunks = [];

    startBtn.onclick = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = event => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                uploadAudio(audioBlob);
            };

            mediaRecorder.start();
            statusMsg.textContent = "🎙️ Recording started...";
        } catch (err) {
            console.error("Microphone access error:", err);
            statusMsg.textContent = "❌ Failed to access microphone.";
        }
    };

    stopBtn.onclick = () => {
        if (mediaRecorder && mediaRecorder.state !== "inactive") {
            mediaRecorder.stop();
            statusMsg.textContent = "🛑 Recording stopped. Uploading...";
        }
    };

    function uploadAudio(blob) {
        const formData = new FormData();
        formData.append("file", blob, "recording.webm");

        fetch("http://localhost:8000/upload-audio", {
            method: "POST",
            body: formData
        })
        .then(async response => {
            if (!response.ok) {
                const err = await response.text();
                throw new Error(`Server error: ${response.status} - ${err}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("✅ Upload response:", data);
            statusMsg.textContent = `✅ Uploaded: ${data.filename}, Type: ${data.content_type}, Size: ${data.size} bytes`;
        })
        .catch(error => {
            console.error("❌ Upload failed:", error);
            statusMsg.textContent = "❌ Upload failed. Check console for details.";
        });
    }
});
