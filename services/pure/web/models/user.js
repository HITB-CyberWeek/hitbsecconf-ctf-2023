const mongoose = require("mongoose");
const bcrypt = require("bcryptjs");
const Schema = mongoose.Schema;

const UserSchema = new Schema({
    _id: {
        type: String,
        required: true
    },
    password: {
        type: String,
        required: true
    }
}, { timestamps: true });

UserSchema.pre("save", async function(next) {
    try {
        const user = this;
        if (!user.isModified("password")) {
            next();
        }

        const salt = await bcrypt.genSalt(10);
        const hashedPassword = await bcrypt.hash(this.password, salt);
        this.password = hashedPassword;
        next();
    } catch (error) {
        return next(error);
    }
});

UserSchema.methods.matchPassword = async function (password) {
    return await bcrypt.compare(password, this.password);
};

UserSchema.virtual('username').get(function() {
    return this._id;
});

UserSchema.index({createdAt: 1}, {expireAfterSeconds: 20*60});

const User = mongoose.model('user', UserSchema);
module.exports = User;
