randomChoice = arr => arr[Math.floor(arr.length * Math.random())];

Array.prototype.minBy = function(pluck) {
	return this.reduce((min, x) => min && pluck(min) <= pluck(x) ? min : x, null)
}

Array.prototype.maxBy = function(pluck) {
	return this.reduce((max, x) => max && pluck(max) >= pluck(x) ? max : x, null)
}

const error = e => alert(e);
const debounce = func => {
	var timer;
	return event => {
		if(timer) clearTimeout(timer);
		timer = setTimeout(func, 1, event);
	};
}
const handleErrors = response => {
	if(!response.ok)
		throw Error(`${response.status} ${response.statusText}`);

	return response;
}

const geolocate = () => new Promise((resolve, reject) => !navigator.permissions
	? reject(new Error("permission API is not supported"))
	: navigator.permissions.query({name: 'geolocation'}).then(permission => permission.state === "granted"
		? navigator.geolocation.getCurrentPosition(pos => resolve(pos?.coords), err => reject(err))
		: resolve(null)));

let geojson = {};
let state = {
	hoverLocation: null,
	hovered: null,
	selected: null,
	places: [],
	route: [],
	builtRoute: []
}

var width, height;

let canvas = document.querySelector('canvas');
let context = d3.select('#content canvas')
	.node()
	.getContext('2d');

var projection = d3.geoOrthographic().rotate([30, -45]);

$id = document.querySelector('#side #id');
$lat = document.querySelector('#side #lat');
$long = document.querySelector('#side #long');
$public = document.querySelector('#side #public');
$secret = document.querySelector('#side #secret');
$save = document.querySelector('#side #save');
$note = document.querySelector('#side #note');

$routeAdd = document.querySelector('#side #route-add');
$routeBuild = document.querySelector('#side #route-build');
$routeClean = document.querySelector('#side #route-clean');
$routeCount = document.querySelector('#side #route-count');

$place = document.querySelector('#place');
$route = document.querySelector('#route');
$routeText = document.querySelector('#route #text');
$routeClose = document.querySelector('#route #route-close');
$route.style.display = 'none';

$routeAdd.disabled = $routeBuild.disabled = $routeClean.disabled = true;
$public.onkeyup = $secret.onkeyup = () => $save.disabled = false;

geolocate().then(coords => {
	const lat = coords?.latitude || 0.0, long = coords?.longitude || 0.0;
	projection.rotate([lat, long - 10.0]);
	fetch(`/api/auth?lat=${encodeURIComponent(lat.toString())}&long=${encodeURIComponent(long.toString())}`)
		.then(handleErrors)
		.then(response => response.text())
		.then(id => get(id, true).then(() => $note.textContent = `your\u00A0current\u00A0place\u00A0is\u00A0${id} with coords φ=${lat}°, λ=${long}°; do you want to save it?`))
		.then(() => fetch(`/api/list`)
			.then(handleErrors)
			.then(response => response.body)
			.then(body => {
				const reader = body.pipeThrough(new TextDecoderStream()).getReader();
				reader.read().then(({done, value}) => {
					value.split('\n')
						.filter(line => !!line.length)
						.forEach(line => state.places.push(JSON.parse(line)));
			}).then(() => update());
		}))
		.catch(e => alert(e?.toString() ?? 'unknown error'))
});

var m0, o0, rotated = false;

const mousedown = e => {
	m0 = [e.pageX, e.pageY];
	o0 = projection.rotate();
	e.preventDefault();
}

const mousemove = e => {
	if (m0) {
		var m1 = [e.pageX, e.pageY],
		o1 = [o0[0] - (m0[0] - m1[0]) / 8, o0[1] - (m1[1] - m0[1]) / 8];
		rotated |= (Math.abs(o1[0] - o0[0]) > 0.01 || Math.abs(o1[1] - o0[1]) > 0.01);
		projection.rotate(o1);
	}

	state.hoverLocation = projection.invert(d3.pointer(e, this))
	update();
}

const mouseup = e => {
	if (!m0) return;

	mousemove(e);
	m0 = null;

	setTimeout(() => rotated = false, 1);
}

const click = e => {
	if(rotated)
		return;

	const pos = d3.pointer(e, this)
	const coords = projection.invert(pos);

	state.selected = state.hovered || {id: null, lat: coords[1], long: coords[0]};

	update();
	updateSidePanel();
}

const init = () => {
	d3.select('canvas')
		.on('click', click)
		.on("mousedown", mousedown);
	d3.select(window)
		.on("mousemove", mousemove)
		.on("mouseup", mouseup);
}

$save.onclick = () => {
	let url = `/api/place`;
	let data = {public: $public.value, secret: $secret.value};
	if(/^[0-9a-f]{64}$/i.test($id.textContent))
		url += '/' + encodeURIComponent($id.textContent);
	else {
		data.lat = Number($lat.textContent);
		data.long = Number($long.textContent);
	}

	fetch(url, {method: 'PUT', body: JSON.stringify(data), headers: {'Content-Type': 'application/json;charset=utf-8'}})
		.then(handleErrors)
		.then(response => response.text())
		.then(id => {
			document.querySelector('#side #id').textContent = id || 'n/a';
			place = {id: id, lat: data.lat, long: data.long};
			state.selected = place;
			state.places.push(place);
			$routeAdd.disabled = state.route.includes(id) || state.route.length >= MAX_ROUTE_LENGTH;
			$save.disabled = true;
		})
		.catch(e => alert(e?.toString() ?? 'unknown error'));
};

const MAX_ROUTE_LENGTH = 10;
$routeAdd.onclick = () => {
	if(!state.selected?.id)
		alert('place not selected');

	if(state.route.length >= MAX_ROUTE_LENGTH)
		alert(`too many places for route (max == ${MAX_ROUTE_LENGTH})`);

	state.route.push(state.selected.id);
	$routeBuild.disabled = false;
	$routeClean.disabled = false;
	$routeAdd.disabled = true;
	$routeCount.textContent = state.route.length;
}

const gotoPhrases = ['Go to', 'Visit', 'Be a guest of', 'Check in at'];
const publicPhrases = ['Here you can see', 'The more interesting things here', 'The best features of this place'];
const secretPhrases = ['Note for yourself', 'NB', 'PS', 'Check the sound', 'The bottom line', 'Small secret'];
$routeBuild.onclick = () => {
	fetch(`/api/route`, {method: 'POST', body: JSON.stringify(state.route), headers: {'Content-Type': 'application/json;charset=utf-8'}})
		.then(handleErrors)
		.then(response => response.body)
		.then(body => {
			let text = [];
			state.builtRoute = [];
			const reader = body.pipeThrough(new TextDecoderStream()).getReader();
			reader.read().then(({done, value}) => {
				value.split('\n').filter(line => !!line.length).forEach(line => {
					const json = JSON.parse(line);
					state.builtRoute.push([json.long, json.lat]);
					text.push(`${randomChoice(gotoPhrases)} φ=${json.lat}°, λ=${json.long}°. ${randomChoice(publicPhrases)}: '${json.public}'. ${randomChoice(secretPhrases)}: '${json.secret}'.`);
				});
			}).then(() => {
				$routeText.textContent = text.join("\n    \u21E9\n") + '\n\nNote: the route may be suboptimal, the route construction algorithm still needs to be improved...';
				$route.style.display = 'block';
				$place.style.display = 'none';
			}).then(() => update());
		})
		.catch(e => alert(e?.toString() ?? 'unknown error'));
}

$routeClose.onclick = () => {
	$routeClean.click();
	$routeText.textContent = '';
	$route.style.display = 'none';
	$place.style.display = 'block';
	state.builtRoute = [];
};

$routeClean.onclick = () => {
	state.route = [];
	$routeBuild.disabled = true;
	$routeClean.disabled = true;
	$routeCount.textContent = state.route.length;
};

const get = (id, my) => fetch(`/api/place/${encodeURIComponent(id)}`)
	.then(handleErrors)
	.then(response => response.json())
	.then(json => {
		$id.textContent = id;
		$lat.textContent = json.lat;
		$long.textContent = json.long;
		$public.value = json.public || '';
		$secret.value = json.secret || '';
		$public.disabled = $secret.disabled = $save.disabled = !my && !json.secret;
	})
	.catch(e => alert(e?.toString() ?? 'unknown error'));

const updateSidePanel = () => {
	const selected = state.selected;
	if(!selected)
		return;

	$note.style.display = 'none';
	const id = selected.id, lat = selected.lat, long = state.selected.long;
	$id.textContent = id || 'not saved yet';
	$lat.textContent = lat;
	$long.textContent = long;

	if(!id) {
		$public.disabled = $secret.disabled = $save.disabled = false;
		$public.value = $secret.value = '';
		return;
	}

	$routeAdd.disabled = state.route.includes(id) || state.route.length >= MAX_ROUTE_LENGTH;
	get(id, false);
}

let geoGenerator = d3.geoPath()
	.projection(projection)
	.pointRadius(5)
	.context(context);

const update = () => {
	if(!geojson.features) return;

	context.clearRect(0, 0, width, height);
	geojson.features.forEach(d => {
		context.beginPath();
		context.fillStyle = '#ccc';
		geoGenerator(d);
		context.fill();
	});

	context.lineWidth = 0.5;
	context.strokeStyle = '#333';

	context.beginPath();
	geoGenerator({type: 'FeatureCollection', features: geojson.features})
	context.stroke();

	let graticule = d3.geoGraticule();
	context.beginPath();
	context.strokeStyle = '#ccc';
	geoGenerator(graticule());
	context.stroke();

	state.builtRoute.map((item, idx) => idx > 0 ? [state.builtRoute[idx - 1], item] : null).filter(item => item != null).forEach(item => {
		context.beginPath();
		context.lineWidth = 1.5;
		context.strokeStyle = '#37f';
		geoGenerator({type: 'Feature', geometry: {type: 'LineString', coordinates: item}});
		context.stroke();
	});

	const loc = state.hoverLocation;
	const hovered = !loc ? undefined : state.places
		.map(place => [place, Math.abs(loc[1] - place.lat), Math.abs(loc[0] - place.long)])
		.filter(item => item[1] < 1.5 && item[2] < 1.5)
		.minBy(item => item[1] + item[2])?.[0];

	state.hovered = hovered;
	document.body.style.cursor = !hovered ? 'auto' : 'pointer';

	const drawPlace = place => {
		context.beginPath();
		context.fillStyle = place === hovered ? '#f75' : place === state.selected ? '#f30' : '#37f';
		d3.geoPath()
			.projection(projection)
			.pointRadius(place === hovered || place === state.selected ? 12 : 6)
			.context(context)({type: 'Feature', geometry: {type: 'Point', coordinates: [place.long, place.lat]}});
		context.fill();
	}

	state.places.forEach(place => drawPlace(place));

	if(state.hovered)
		drawPlace(state.hovered);
	if(state.selected)
		drawPlace(state.selected);
}

const SIDE_WIDTH = 400;
const resize = () => {
	width = window.innerWidth - SIDE_WIDTH;
	height = window.innerHeight;

	canvas.width = width;
	canvas.height = height;

	projection = projection
		.scale(600 * Math.min(width / 1920.0, height / 1080.0))
		.translate([width / 2, height / 2]);

	update();
}

window.addEventListener('resize', debounce(() => resize()));
resize();

d3.json("earth.json").then(json => {
	geojson = json;
	init();
	update();
});
