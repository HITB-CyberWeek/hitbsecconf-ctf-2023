const mongoose = require("mongoose");

mongoose.Promise = global.Promise;

const connect = async (dbUrl) => {
    mongoose.connect(dbUrl, { useNewUrlParser: true, useUnifiedTopology: true });
    const db = mongoose.connection;
    db.on("error", () => {
        console.error("Could not connect to MongoDB");
    });
    db.once("open", () => {
        console.log("Successfully connected to MongoDB");
   });
};

module.exports = { connect };
