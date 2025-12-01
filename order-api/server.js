const express = require('express');
const cors = require('cors');

const app = express();
const PORT = 3000;

app.use(cors());
app.use(express.json());

let orders = [];

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

app.get('/', (req, res) => {
  res.json({ 
    message: 'API de Pedidos - Jitterbit',
    status: 'Funcionando! 🚀',
    endpoints: {
      create: 'POST /order',
      get: 'GET /order/:orderId',
      list: 'GET /order/list/all'
    }
  });
});

app.post('/order', (req, res) => {
  try {
    const { numeroPedido, valorTotal, dataCriacao, items } = req.body;

    if (!numeroPedido || !valorTotal || !dataCriacao || !items) {
      return res.status(400).json({ error: 'Campos obrigatórios faltando' });
    }

    const existingOrder = orders.find(order => order.orderId === numeroPedido);
    if (existingOrder) {
      return res.status(409).json({ error: 'Pedido já existe' });
    }

    const transformedData = transformOrderData(req.body);
    orders.push(transformedData);

    res.status(201).json({ 
      message: 'Pedido criado com sucesso!',
      order: transformedData 
    });
  } catch (error) {
    res.status(500).json({ error: 'Erro interno do servidor' });
  }
});

app.get('/order/:orderId', (req, res) => {
  const { orderId } = req.params;
  const order = orders.find(order => order.orderId === orderId);
  
  if (!order) {
    return res.status(404).json({ error: 'Pedido não encontrado' });
  }
  
  res.json(order);
});

app.get('/order/list/all', (req, res) => {
  res.json({ 
    count: orders.length,
    orders: orders
  });
});

app.listen(PORT, () => {
  console.log('🚀 Servidor rodando na porta ' + PORT);
  console.log('📊 Acesse: http://localhost:' + PORT + '/');
});
