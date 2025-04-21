const socket = io("http://localhost:5000/");
const avatar = document.getElementById('avatar');
const caption = document.getElementById('caption');
let talking = false;
let loop = true;

socket.on('finished', () => {
    console.log("\nfinished")
    loop = false;
});

socket.on('new_caption', (data) => {
    console.log("\nnew_caption")
    loop = true; // restart loop
    caption.textContent = data.text;
    animateAvatar();
});

function stopAvatar() {
    avatar.src = '/static/avatar1.png';
    talking = false;
}

function animateAvatar() {
    if (talking) return;
    talking = true;
    let toggle = true;

    function continueLoop() {
        if (!loop) {
            stopAvatar();
            return;
        }
        avatar.src = toggle ? '/static/avatar2.png' : '/static/avatar1.png';
        toggle = !toggle;
        setTimeout(continueLoop, 150);
    }
    continueLoop();
}


