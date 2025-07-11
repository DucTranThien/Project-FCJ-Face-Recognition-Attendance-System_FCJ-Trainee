class CameraCapture {
    constructor(videoId, canvasId, captureBtn, submitBtn) {
        this.video = document.getElementById(videoId);
        this.canvas = document.getElementById(canvasId);
        this.captureBtn = document.getElementById(captureBtn);
        this.submitBtn = document.getElementById(submitBtn);
        this.stream = null;
        this.capturedImage = null;
        
        this.init();
    }
    
    async init() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({ 
                video: { width: 640, height: 480 } 
            });
            this.video.srcObject = this.stream;
            
            this.captureBtn.addEventListener('click', () => this.captureImage());
            this.submitBtn.addEventListener('click', (e) => this.handleSubmit(e));
        } catch (err) {
            console.error('Camera access denied:', err);
            alert('Camera access is required for face capture');
        }
    }
    
    captureImage() {
        const context = this.canvas.getContext('2d');
        this.canvas.width = this.video.videoWidth;
        this.canvas.height = this.video.videoHeight;
        context.drawImage(this.video, 0, 0);
        
        this.capturedImage = this.canvas.toDataURL('image/jpeg', 0.8);
        this.canvas.style.display = 'block';
        this.video.style.display = 'none';
        this.captureBtn.textContent = 'Retake';
        this.submitBtn.disabled = false;
    }
    
    handleSubmit(e) {
        if (!this.capturedImage) {
            e.preventDefault();
            alert('Please capture an image first');
            return;
        }
        
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = 'face_image_data';
        hiddenInput.value = this.capturedImage;
        
        e.target.closest('form').appendChild(hiddenInput);
    }
    
    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
        }
    }
}