const express = require('express');
const router = express.Router();
const Order = require('../models/Order');

const transformOrderData = (input) => {
  return {
    orderId: input.numeroPedido,
    value: input.valorTotal,
    creationDate: new Date(input.dataCriacao),
    items: input.items.map(item => ({
      productId: parseInt(item.idItem),
      quantity: item.quantidadeItem,
      price: item.valorItem
    }))
  };
};

router.post('/', async (req, res) => {
  try {
    const { numeroPedido, valorTotal, dataCriacao, items } = req.body;

    if (!numeroPedido || !valorTotal || !dataCriacao || !items) {
      return res.status(400).json({ error: 'Campos obrigatórios faltando' });
    }

    const existingOrder = await Order.findOne({ orderId: numeroPedido });
    if (existingOrder) {
      return res.status(409).json({ error: 'Pedido já existe' });
    }

    const transformedData = transformOrderData(req.body);
    const newOrder = new Order(transformedData);
    const savedOrder = await newOrder.save();

    res.status(201).json({ message: 'Pedido criado com sucesso', order: savedOrder });
  } catch (error) {
    res.status(500).json({ error: 'Erro interno do servidor' });
  }
});

router.get('/:orderId', async (req, res) => {
  try {
    const { orderId } = req.params;
    const order = await Order.findOne({ orderId });
    
    if (!order) return res.status(404).json({ error: 'Pedido não encontrado' });
    res.json(order);
  } catch (error) {
    res.status(500).json({ error: 'Erro interno do servidor' });
  }
});

router.get('/list/all', async (req, res) => {
  try {
    const orders = await Order.find().sort({ creationDate: -1 });
    res.json({ count: orders.length, orders });
  } catch (error) {
    res.status(500).json({ error: 'Erro interno do servidor' });
  }
});

module.exports = router;
