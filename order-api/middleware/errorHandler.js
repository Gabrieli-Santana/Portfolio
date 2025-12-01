const errorHandler = (err, req, res, next) => {
  console.error('Erro:', err);

  if (err.name === 'ValidationError') {
    const errors = Object.values(err.errors).map(error => error.message);
    return res.status(400).json({ error: 'Erro de validação', details: errors });
  }

  if (err.code === 11000) {
    return res.status(409).json({ error: 'OrderId já existe' });
  }

  res.status(500).json({ error: 'Erro interno do servidor' });
};

module.exports = errorHandler;
