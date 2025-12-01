const mongoose = require('mongoose');

const itemSchema = new mongoose.Schema({
  productId: { type: Number, required: true },
  quantity: { type: Number, required: true, min: 1 },
  price: { type: Number, required: true, min: 0 }
});

const orderSchema = new mongoose.Schema({
  orderId: { type: String, required: true, unique: true },
  value: { type: Number, required: true, min: 0 },
  creationDate: { type: Date, required: true },
  items: [itemSchema]
}, { timestamps: true });

orderSchema.index({ orderId: 1 });

module.exports = mongoose.model('Order', orderSchema);
