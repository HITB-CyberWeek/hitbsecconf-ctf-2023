const avatars = new Map();

Map.prototype.getOrAdd = function(key, promise) {
  const value = this.get(key);
  return !value ? promise.then(val => this[key] = val) : Promise.resolve(value);
}

const $space = document.getElementById('space-id');
const $msg = document.querySelector('button#msg');
const $text = document.querySelector('textarea');
const $gen = document.getElementById('generate');
const $join = document.getElementById('join');
const $room = document.getElementById('room');
const $close = document.getElementById('close');

var ws;

$gen.onclick = () => ws.send(JSON.stringify({type: 'generate'}));
$join.onclick = () => {
  let name = prompt("Enter existing space id or leave blank to generate random space");
  if(name === null) return;
  $chat.replaceChildren();
  ws.send(JSON.stringify({type: 'join', data: name}));
}
$room.onclick = () => {
  let name;
  do {
    name = prompt("Enter room name /[a-z]+/i, or leave blank to return to space root");
  } while(name?.length > 0 && !/[a-z]+/i.test(name));
  if(name === null) return;
  $chat.replaceChildren();
  ws.send(JSON.stringify({type: 'room', data: name}));
}
$msg.onclick = () => {
  if(!!$text.value?.length) {
    ws.send(JSON.stringify({type: 'msg', data: $text.value}));
    $text.value = "";
  }
}
$close.onclick = () => ws.send(JSON.stringify({type: 'close'}));
$text.onkeydown = e => {
  if(e.ctrlKey && e.key === 'Enter')
  {
    e.preventDefault();
    $msg.click();
  }
}

const $container = document.getElementById('chat-container');
const $chat = document.getElementById('chat');
const add = (msg) => {
  if(!msg) return;

  if(msg.type === 'close') {
    $close.disabled = true;
  }

  if(msg.type === 'join' && msg.context?.length) {
    $space.textContent = msg.context;
    $room.disabled = false;
    $text.disabled = false;
    $msg.disabled = false;
    $close.disabled = false;
    $gen.disabled = true;
  }

  const avatar = msg.avatar;
  (!avatar ? Promise.resolve() : avatars.getOrAdd(avatar, toBlob(avatar).then(blob => URL.createObjectURL(blob)))).then(url => {
    const template = document.getElementById('msg-template').content;
    template.querySelector('.msg-date').textContent = new Date(msg.time).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
    template.querySelector('.msg-name').textContent = msg.author;
    template.querySelector('.msg-text').textContent = msg.text;
    template.querySelector('.avatar').src = url || 'default.png';
    template.querySelector('.msg-content').classList[msg.type === 'error' ? "add" : "remove"]('system');
    template.querySelector('.msg-content').classList[msg.type !== 'msg' && msg.type !== 'error' ? "add" : "remove"]('aux');
    const $clone = document.importNode(template, true);
    $chat.append($clone);
    $container.scrollTop = $container.scrollHeight;
  });
}

function connect() {
  ws = new WebSocket(`${/^https:/i.test(location.href) ? 'wss' : 'ws'}://${location.host}/ws`);
  ws.onmessage = msg => add(JSON.parse(msg.data));
  ws.onclose = _ => setTimeout(connect, 60000);
  ws.onerror = err => {
    console.error('ws error: ', err.message, 'closing socket');
    ws.close();
  };
}

connect();

// Colour Alphabet: https://eleanormaclure.files.wordpress.com/2011/03/colour-coding.pdf
const palette = {
  '0': {rgb: [255, 255, 255], hex: '#FFFFFF', name: 'White'},
  'A': {rgb: [240, 163, 255], hex: '#F0A3FF', name: 'Amethyst'},
  'B': {rgb: [0, 117, 220], hex: '#0075DC', name: 'Blue'},
  'C': {rgb: [153, 63, 0], hex: '#993F00', name: 'Caramel'},
  'D': {rgb: [76, 0, 92], hex: '#4C005C', name: 'Damson'},
  'E': {rgb: [25, 25, 25], hex: '#191919', name: 'Ebony'},
  'F': {rgb: [0, 92, 49], hex: '#005C31', name: 'Forest'},
  'G': {rgb: [43, 206, 72], hex: '#2BCE48', name: 'Green'},
  'H': {rgb: [255, 204, 153], hex: '#FFCC99', name: 'Honeydew'},
  'I': {rgb: [128, 128, 128], hex: '#808080', name: 'Iron'},
  'J': {rgb: [148, 255, 181], hex: '#94FFB5', name: 'Jade'},
  'K': {rgb: [143, 124, 0], hex: '#8F7C00', name: 'Khaki'},
  'L': {rgb: [157, 204, 0], hex: '#9DCC00', name: 'Lime'},
  'M': {rgb: [194, 0, 136], hex: '#C20088', name: 'Mallow'},
  'N': {rgb: [0, 51, 128], hex: '#003380', name: 'Navy'},
  'O': {rgb: [255, 164, 5], hex: '#FFA405', name: 'Orpiment'},
  'P': {rgb: [255, 168, 187], hex: '#FFA8BB', name: 'Pink'},
  'Q': {rgb: [66, 102, 0], hex: '#426600', name: 'Quagmire'},
  'R': {rgb: [255, 0, 16], hex: '#FF0010', name: 'Red'},
  'S': {rgb: [94, 241, 242], hex: '#5EF1F2', name: 'Sky'},
  'T': {rgb: [0, 153, 143], hex: '#00998F', name: 'Turquoise'},
  'U': {rgb: [224, 255, 102], hex: '#E0FF66', name: 'Uranium'},
  'V': {rgb: [116, 10, 255], hex: '#740AFF', name: 'Violet'},
  'W': {rgb: [153, 0, 0], hex: '#990000', name: 'Wine'},
  'X': {rgb: [255, 255, 128], hex: '#FFFF80', name: 'Xanthin'},
  'Y': {rgb: [255, 225, 0], hex: '#FFE100', name: 'Yellow'},
  'Z': {rgb: [255, 80, 5], hex: '#FF5005', name: 'Zinnia'},
};
let toBlob = (avatar) => {
  const size = Math.sqrt(avatar.length);
  const width = size, height = size;

  const canvas = new OffscreenCanvas(width, height);
  const ctx = canvas.getContext("2d");

  const img = ctx.createImageData(width, height);
  let data = img.data;

  for(let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      let i = y * width + x;
      let idx = 4 * i;
      let color = palette[avatar[i]] || palette['0'];
      data[idx + 0] = color.rgb[0]
      data[idx + 1] = color.rgb[1];
      data[idx + 2] = color.rgb[2];
      data[idx + 3] = 255;
    }
  }

  ctx.putImageData(img, 0, 0);

  return canvas.convertToBlob({type: "image/png"});
}
