const mongoose = require("mongoose");
const moment = require("moment");
const Schema = mongoose.Schema;

const CardSchema = new Schema({
    user: {
        type: String,
        required: true,
        index: true
    },
    firstName: {
        type: String
    },
    lastName: {
        type: String
    },
    organization: {
        type: String
    },
    title: {
        type: String
    },
    email: {
        type: String
    },
    phone: {
        type: String
    },
    comment: {
        type: String
    }
}, { timestamps: true });

CardSchema.virtual('formattedUpdatedAt').get(function() {
    if (this.updatedAt) {
        return moment(this.updatedAt).format();
    }
    return '<empty>';
});

CardSchema.index({createdAt: 1}, {expireAfterSeconds: 20*60});

const Card = mongoose.model('card', CardSchema);
module.exports = Card;
