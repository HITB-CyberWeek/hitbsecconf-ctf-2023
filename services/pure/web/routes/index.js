const express = require('express');
const passport = require('passport');
const Card = require('../models/card');

const router = express.Router();

var ensureAuthenticated = function (req, res, next) {
    if (req.user) {
        next();
    } else {
        req.session.redirectTo = req.path;
        res.redirect('/login');
    }
};

var buildCardModel = function (req) {
    var model = { user: req.user.username };

    if (req.body.firstName) {
        model.firstName = req.body.firstName;
    }

    if (req.body.lastName) {
        model.lastName = req.body.lastName;
    }

    if (req.body.organization) {
        model.organization = req.body.organization;
    }

    if (req.body.title) {
        model.title = req.body.title;
    }

    if (req.body.email) {
        model.email = req.body.email;
    }

    if (req.body.phone) {
        model.phone = req.body.phone;
    }

    if (req.body.comment) {
        model.comment = req.body.comment;
    }

    return model;
};

router.get('/register', (req, res) => {
    var model = {};
    if (req.session.messages) {
        model.error = req.session.messages[0];
        delete req.session.messages;
    }

    if (req.session.username) {
        model.username = req.session.username;
        delete req.session.username;
    }

    model.darkMode = req.session.darkMode == 1;

    res.render('register', model);
});
router.post('/register',
    function(req, res, next) {
        if (req.body.username) {
            req.session.username = req.body.username;
        }
        next();
    },
    passport.authenticate('local-signup', { failureRedirect: '/register', failureMessage: true }),
    function(req, res, next) {
        var redirectTo = req.session.redirectTo || '/';
        delete req.session.redirectTo;
        delete req.session.username;
        res.redirect(redirectTo);
});


router.get('/login', (req, res) => {
    var model = {};
    if (req.session.messages) {
        model.error = req.session.messages[0];
        delete req.session.messages;
    }

    if (req.session.username) {
        model.username = req.session.username;
        delete req.session.username;
    }

    model.darkMode = req.session.darkMode == 1;

    res.render('login', model);
});
router.post('/login',
    function(req, res, next) {
        if (req.body.username) {
            req.session.username = req.body.username;
        }
        next();
    },
    passport.authenticate('local-login', { failureRedirect: '/login', failureMessage: true }),
    function(req, res, next) {
        var redirectTo = req.session.redirectTo || '/';
        delete req.session.redirectTo;
        delete req.session.username;
        res.redirect(redirectTo);
});

router.get('/logout', (req, res, next) => {
    req.logout(function(err) {
        if (err) { return next(err); }
        res.redirect('/');
    });
});

router.get('/', ensureAuthenticated, async (req, res) => {
    var cards;
    if (req.session.isAdmin) {
        cards = await Card.find({}).sort({ user: 1, firstName: 1, lastName: 1, updatedAt: -1 });
    } else {
        cards = await Card.find({user: req.user.username}).sort({ firstName: 1, lastName: 1, updatedAt: -1 });
    }
    res.render('index', { user : req.user, cards: cards, isAdmin: req.session.isAdmin, darkMode: req.session.darkMode == 1 });
});

router.get('/edit/:id', ensureAuthenticated, async (req, res) => {
    var filter = { _id: req.params.id };
    if (!req.session.isAdmin) {
        filter['user'] = req.user.username;
    }

    const card = await Card.findOne(filter);
    if (!card) {
        res.status(404).send('Card not found');
    } else {
        res.render('edit', { user : req.user, action: `/edit/${req.params.id}`, card: card, isAdmin: req.session.isAdmin, darkMode: req.session.darkMode == 1 });
    }
});
router.post('/edit/:id', ensureAuthenticated, async (req, res) => {
    var filter = { _id: req.params.id };
    if (!req.session.isAdmin) {
        filter['user'] = req.user.username;
    }

    var r = await Card.updateOne(filter, buildCardModel(req));
    if (r && r.matchedCount == 0) {
        res.status(404).send('Card not found');
    } else {
        res.redirect('/');
    }
});

router.get('/add', ensureAuthenticated, (req, res) => {
    res.render('edit', { user: req.user, action: '/add', card: {}, isAdmin: req.session.isAdmin, darkMode: req.session.darkMode == 1 });
});
router.post('/add', ensureAuthenticated, async (req, res) => {
    await Card.create(buildCardModel(req));
    res.redirect('/');
});

router.get('/delete/:id', ensureAuthenticated, async (req, res) => {
    var filter = { _id: req.params.id };
    if (!req.session.isAdmin) {
        filter['user'] = req.user.username;
    }

    var r = await Card.deleteOne(filter);
    if (r && r.deletedCount == 0) {
        res.status(404).send('Card not found');
    } else {
        res.redirect('/');
    }
});

module.exports = router;
