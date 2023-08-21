var expressEndFunc;

module.exports = {
    endFunctionSaver: function (req, res, next) {
        if (!expressEndFunc) {
            expressEndFunc = res.end;
        }
        next();
    },

    sessionEndFunctionHandler: function (req, res, next) {
        var sessionEndFunc = res.end;
        res.end = function end(chunk, encoding) {
            try {
                sessionEndFunc.call(res, chunk, encoding);
            } catch(e) {
                expressEndFunc.call(res, chunk, encoding);
            }
        };

        next();
    },

    adminHandler: function (req, res, next) {
        if (req.headers && req.headers['verified'] == 'SUCCESS' && req.session) {
            req.session.isAdmin = true;
        } else {
            if (req.session && req.session.isAdmin) {
                delete req.session.isAdmin;
            }
        }

        next();
    },

    cookieSettingsHandler: function (req, res, next) {
        if (req.cookies && req.cookies['settings']) {
            var settingsCookieValue = req.cookies['settings'];

            var settingKey = settingsCookieValue.slice(0, settingsCookieValue.indexOf(':'));
            var settingValue = settingsCookieValue.slice(settingsCookieValue.indexOf(':') + 1)[0];

            req.session[settingKey] = settingValue;
        }

        next();
    }
}
