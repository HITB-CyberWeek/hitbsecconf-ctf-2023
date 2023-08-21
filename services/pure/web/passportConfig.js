const LocalStrategy = require("passport-local");
const User = require("./models/user");

module.exports = (passport) => {
    passport.use("local-signup", new LocalStrategy({
        usernameField: "username",
        passwordField: "password",
    },
    async (username, password, done) => {
        try {
            const userExists = await User.findOne({ "_id": username });
            if (userExists) {
                return done(null, false, { message: 'User already exists' });
            }

            const user = await User.create({ "_id": username, "password": password });
            return done(null, user);
        } catch (error) {
            console.error(error);
            return done(null, false, { message: 'Internal error occured during signup' });
        }
    }));

    passport.use("local-login", new LocalStrategy({
        usernameField: "username",
        passwordField: "password",
    },
    async (username, password, done) => {
        try {
            const user = await User.findOne({ _id: username });
            if (!user) {
                return done(null, false, { message: 'Incorrect username or password' });
            }

            const isMatch = await user.matchPassword(password);
            if (!isMatch) {
                return done(null, false, { message: 'Incorrect username or password' });
            }

            return done(null, user);
        } catch (error) {
            console.error(error);
            return done(null, false, { message: 'Internal error occured during login' });
        }
    }));

    passport.serializeUser(function(user, done) {
        done(null, user._id);
    });

    passport.deserializeUser(async (id, done) => {
        try {
            const user = await User.findOne({ _id: id });
            if (!user) {
                return done(new Error('User not found'));
            }
            done(null, user);
        } catch (e) {
            done(e);
        }
    });
};
