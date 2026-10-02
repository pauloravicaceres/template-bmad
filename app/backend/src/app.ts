import express from 'express';
import cors from 'cors';
import { errorHandler } from './middlewares/errorHandler';
import serviciosRouter from './routes/servicios.routes';

const app = express();

app.use(cors());
app.use(express.json());

app.use('/api/v1/servicios', serviciosRouter);

app.use(errorHandler);

export default app;
