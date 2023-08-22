const express = require('express');
const path = require('path');
const session = require('express-session');
const MongoStore = require('connect-mongo');
const cookieParser = require('cookie-parser');
const bodyParser = require('body-parser');
const passport = require('passport');
const LocalStrategy = require('passport-local');
const routes = require('./routes/index');
const middlewares = require('./middlewares');
const db = require('./db');
const passportConfig = require('./passportConfig')

const app = express();

app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'pug');

app.use(cookieParser());

app.use(middlewares.endFunctionSaver);
app.use(session({
    secret: process.env.SESSION_SECRET,
    resave: false,
    saveUninitialized: true,
    store: MongoStore.create({ mongoUrl: process.env.MONGODB_URL }),
    cookie: {
        maxAge: 20*60*1000
    }
}));
app.use(middlewares.sessionEndFunctionHandler);

app.use(bodyParser.urlencoded({ extended: false }))

app.use(middlewares.adminHandler);
app.use(middlewares.cookieSettingsHandler);

app.use(passport.initialize());
app.use(passport.session());

app.use('/', routes);

passportConfig(passport);

db.connect(process.env.MONGODB_URL);

app.listen(3000);
