let timer;
const tabs = document.querySelectorAll('[data-tab-target]')
const tabContents = document.querySelectorAll('[data-tab-content]')

tabs.forEach(tab => {
  tab.addEventListener('click', () => {
    const target = document.querySelector(tab.dataset.tabTarget)
    tabContents.forEach(tabContent => {
      tabContent.classList.remove('active')
    })
    tabs.forEach(tab => {
      tab.classList.remove('active')
    })
    tab.classList.add('active')
    target.classList.add('active')
  })
})


document.addEventListener('input', e => {
  const el = e.target;
  
  if( el.matches('[data-color]') ) {
    clearTimeout(timer);
    timer = setTimeout(() => {
      document.documentElement.style.setProperty(`--color-${el.dataset.color}`, el.value);
    }, 100)
  }
})

var c = document.getElementById('c');
var w = c.width = window.innerWidth,
    h = c.height = window.innerHeight,
    ctx = c.getContext('2d'),

    minDist = 10,
    maxDist = 30,
    initialWidth = 10,
    maxLines = 80,
    initialLines = 10,
    speed = 5,

    lines = [],
    frame = 0,
    timeSinceLast = 0,

    dirs = [
        [0, 1], [1, 0], [0, -1], [-1, 0],
        [0.7, 0.7], [0.7, -0.7], [-0.7, 0.7], [-0.7, -0.7]
    ],
    starter = {
        x: w / 2,
        y: h / 2,
        vx: 0,
        vy: 0,
        width: initialWidth
    };

function init() {
    lines.length = 0;

    for (var i = 0; i < initialLines; ++i)
        lines.push(new Line(starter));

    ctx.fillStyle = '#222';
    ctx.fillRect(0, 0, w, h);
}

function getColor(x) {
    return 'hsl(hue, 80%, 50%)'.replace('hue', x / w * 360 + frame);
}

function anim() {
    window.requestAnimationFrame(anim);

    ++frame;

    ctx.shadowBlur = 0;
    ctx.fillStyle = 'rgba(0,0,0,.02)';
    ctx.fillRect(0, 0, w, h);
    ctx.shadowBlur = .5;

    for (var i = 0; i < lines.length; ++i)
        if (lines[i].step()) {
            lines.splice(i, 1);
            --i;
        }

    ++timeSinceLast;

    if (lines.length < maxLines && timeSinceLast > 10 && Math.random() < .5) {
        timeSinceLast = 0;
        lines.push(new Line(starter));

        ctx.fillStyle = ctx.shadowColor = getColor(starter.x);
        ctx.beginPath();
        ctx.arc(starter.x, starter.y, initialWidth, 0, Math.PI * 2);
        ctx.fill();
    }
}

function Line(parent) {
    this.x = parent.x | 0;
    this.y = parent.y | 0;
    this.width = parent.width / 1.25;

    do {
        var dir = dirs[(Math.random() * dirs.length) | 0];
        this.vx = dir[0];
        this.vy = dir[1];
    } while (
        (this.vx === -parent.vx && this.vy === -parent.vy) || (this.vx === parent.vx && this.vy === parent.vy)
    );

    this.vx *= speed;
    this.vy *= speed;
    this.dist = (Math.random() * (maxDist - minDist) + minDist);
}

Line.prototype.step = function () {
    var dead = false;
    var prevX = this.x,
        prevY = this.y;

    this.x += this.vx;
    this.y += this.vy;

    --this.dist;

    if (this.x < 0 || this.x > w || this.y < 0 || this.y > h)
        dead = true;

    if (this.dist <= 0 && this.width > 1) {
        this.dist = Math.random() * (maxDist - minDist) + minDist;

        if (lines.length < maxLines) lines.push(new Line(this));
        if (lines.length < maxLines && Math.random() < .5) lines.push(new Line(this));

        if (Math.random() < .2) dead = true;
    }

    ctx.strokeStyle = ctx.shadowColor = getColor(this.x);
    ctx.beginPath();
    ctx.lineWidth = this.width;
    ctx.moveTo(this.x, this.y);
    ctx.lineTo(prevX, prevY);
    ctx.stroke();

    if (dead) return true;
}

init();
anim();

window.addEventListener('resize', function () {
    w = c.width = window.innerWidth;
    h = c.height = window.innerHeight;
    starter.x = w / 2;
    starter.y = h / 2;
    init();
});

function showRestText() {
    var restText = document.getElementById('rest-text');
    restText.classList.add('show');
}

setTimeout(showRestText, 1000); // Show the rest of the text after 1 second

function hideSplashScreen() {
    var splashScreen = document.getElementById('splash-screen');
    splashScreen.classList.add('fade-out');
    splashScreen.addEventListener('animationend', removeSplashScreen); // Remove splash screen after fade-out animation ends
}

function removeSplashScreen() {
    var splashScreen = document.getElementById('splash-screen');
    splashScreen.remove();
    showMainContent();
}

function showMainContent() {
    var mainContent = document.getElementById('main-content');
    mainContent.classList.add('show');
}



setTimeout(hideSplashScreen, 1); // Hide the splash screen after 3 seconds
