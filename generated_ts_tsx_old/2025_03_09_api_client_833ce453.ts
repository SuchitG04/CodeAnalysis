import * as express from 'express';
import * as WebSocket from 'ws';
import * as jwt from 'jsonwebtoken';
import * as helmet from 'helmet';
import * as cors from 'cors';
import * as morgan from 'morgan';
import * as winston from 'winston';
import * as mongoose from 'mongoose';
import { CircuitBreaker } from 'circuit-breaker-js';

interface User {
  username: string;
  password: string;
  email: string;
}

interface PatientRecord {
  patientId: string;
  medicalHistory: string;
  insuranceClaims: string;
}

interface Subscription {
  subscriptionId: string;
  patientId: string;
  subscriptionStatus: string;
}

class HealthcarePlatform {
  private app: express.Application;
  private wss: WebSocket.Server;
  private circuitBreaker: CircuitBreaker;
  private logger: winston.Logger;

  constructor() {
    this.app = express();
    this.app.use(helmet());
    this.app.use(cors());
    this.app.use(morgan('combined'));
    this.app.use(express.json());

    this.wss = new WebSocket.Server({ port: 8080 });

    this.circuitBreaker = new CircuitBreaker({
      timeout: 3000,
      threshold: 5,
      window: 60000,
    });

    this.logger = winston.createLogger({
      level: 'info',
      format: winston.format.json(),
      transports: [
        new winston.transports.Console(),
        new winston.transports.File({ filename: 'error.log', level: 'error' }),
        new winston.transports.File({ filename: 'combined.log' }),
      ],
    });
  }

  async start() {
    try {
      await mongoose.connect('mongodb://localhost:27017/healthcare-platform');
      this.logger.info('Connected to MongoDB');

      this.app.post('/login', this.login);
      this.app.post('/register', this.register);
      this.app.post('/patient-record', this.createPatientRecord);
      this.app.get('/patient-record/:patientId', this.getPatientRecord);
      this.app.put('/patient-record/:patientId', this.updatePatientRecord);
      this.app.delete('/patient-record/:patientId', this.deletePatientRecord);

      this.app.post('/subscription', this.createSubscription);
      this.app.get('/subscription/:subscriptionId', this.getSubscription);
      this.app.put('/subscription/:subscriptionId', this.updateSubscription);
      this.app.delete('/subscription/:subscriptionId', this.deleteSubscription);

      this.wss.on('connection', (ws) => {
        ws.on('message', (message) => {
          this.handleWebSocketMessage(message);
        });
      });

      this.app.listen(3000, () => {
        this.logger.info('Server listening on port 3000');
      });
    } catch (error) {
      this.logger.error('Error starting server:', error);
      process.exit(1);
    }
  }

  private async login(req: express.Request, res: express.Response) {
    try {
      const { username, password } = req.body;
      const user = await this.getUserByUsername(username);
      if (!user || user.password !== password) {
        return res.status(401).json({ error: 'Invalid username or password' });
      }
      const token = jwt.sign({ username }, 'secret-key', { expiresIn: '1h' });
      return res.json({ token });
    } catch (error) {
      this.logger.error('Error logging in:', error);
      return res.status(500).json({ error: 'Internal Server Error' });
    }
  }

  private async register(req: express.Request, res: express.Response) {
    try {
      const { username, password, email } = req.body;
      const user = await this.createUser(username, password, email);
      return res.json({ user });
    } catch (error) {
      this.logger.error('Error registering:', error);
      return res.status(500).json({ error: 'Internal Server Error' });
    }
  }

  private async createPatientRecord(req: express.Request, res: express.Response) {
    try {
      const { patientId, medicalHistory, insuranceClaims } = req.body;
      const patientRecord = await this.createPatientRecord(patientId, medicalHistory, insuranceClaims);
      return res.json({ patientRecord });
    } catch (error) {
      this.logger.error('Error creating patient record:', error);
      return res.status(500).json({ error: 'Internal Server Error' });
    }
  }

  private async getPatientRecord(req: express.Request, res: express.Response) {
    try {
      const { patientId } = req.params;
      const patientRecord = await this.getPatientRecord(patientId);
      return res.json({ patientRecord });
    } catch (error) {
      this.logger.error('Error getting patient record:', error);
      return res.status(500).json({ error: 'Internal Server Error' });
    }
  }

  private async updatePatientRecord(req: express.Request, res: express.Response) {
    try {
      const { patientId } = req.params;
      const { medicalHistory, insuranceClaims } = req.body;
      const patientRecord = await this.updatePatientRecord(patientId, medicalHistory, insuranceClaims);
      return res.json({ patientRecord });
    } catch (error) {
      this.logger.error('Error updating patient record:', error);
      return res.status(500).json({ error: 'Internal Server Error' });
    }
  }

  private async deletePatientRecord(req: express.Request, res: express.Response) {
    try {
      const { patientId } = req.params;
      await this.deletePatientRecord(patientId);
      return res.json({ message: 'Patient record deleted successfully' });
    } catch (error) {
      this.logger.error('Error deleting patient record:', error);
      return res.status(500).json({ error: 'Internal Server Error' });
    }
  }

  private async createSubscription(req: express.Request, res: express.Response) {
    try {
      const { patientId, subscriptionStatus } = req.body;
      const subscription = await this.createSubscription(patientId, subscriptionStatus);
      return res.json({ subscription });
    } catch (error) {
      this.logger.error('Error creating subscription:', error);
      return res.status(500).json({ error: 'Internal Server Error' });
    }
  }

  private async getSubscription(req: express.Request, res: express.Response) {
    try {
      const { subscriptionId } = req.params;
      const subscription = await this.getSubscription(subscriptionId);
      return res.json({ subscription });
    } catch (error) {
      this.logger.error('Error getting subscription:', error);
      return res.status(500).json({ error: 'Internal Server Error' });
    }
  }

  private async updateSubscription(req: express.Request, res: express.Response) {
    try {
      const { subscriptionId } = req.params;
      const { subscriptionStatus } = req.body;
      const subscription = await this.updateSubscription(subscriptionId, subscriptionStatus);
      return res.json({ subscription });
    } catch (error) {
      this.logger.error('Error updating subscription:', error);
      return res.status(500).json({ error: 'Internal Server Error' });
    }
  }

  private async deleteSubscription(req: express.Request, res: express.Response) {
    try {
      const { subscriptionId } = req.params;
      await this.deleteSubscription(subscriptionId);
      return res.json({ message: 'Subscription deleted successfully' });
    } catch (error) {
      this.logger.error('Error deleting subscription:', error);
      return res.status(500).json({ error: 'Internal Server Error' });
    }
  }

  private async handleWebSocketMessage(message: string) {
    try {
      const { type, data } = JSON.parse(message);
      switch (type) {
        case 'create-patient-record':
          await this.createPatientRecord(data.patientId, data.medicalHistory, data.insuranceClaims);
          break;
        case 'update-patient-record':
          await this.updatePatientRecord(data.patientId, data.medicalHistory, data.insuranceClaims);
          break;
        case 'delete-patient-record':
          await this.deletePatientRecord(data.patientId);
          break;
        default:
          this.logger.error('Unknown WebSocket message type:', type);
      }
    } catch (error) {
      this.logger.error('Error handling WebSocket message:', error);
    }
  }

  private async getUserByUsername(username: string): Promise<User | null> {
    try {
      const user = await mongoose.model('User').findOne({ username });
      return user;
    } catch (error) {
      this.logger.error('Error getting user by username:', error);
      return null;
    }
  }

  private async createUser(username: string, password: string, email: string): Promise<User> {
    try {
      const user = new mongoose.model('User')({ username, password, email });
      await user.save();
      return user;
    } catch (error) {
      this.logger.error('Error creating user:', error);
      throw error;
    }
  }

  private async createPatientRecord(patientId: string, medicalHistory: string, insuranceClaims: string): Promise<PatientRecord> {
    try {
      const patientRecord = new mongoose.model('PatientRecord')({ patientId, medicalHistory, insuranceClaims });
      await patientRecord.save();
      return patientRecord;
    } catch (error) {
      this.logger.error('Error creating patient record:', error);
      throw error;
    }
  }

  private async getPatientRecord(patientId: string): Promise<PatientRecord | null> {
    try {
      const patientRecord = await mongoose.model('PatientRecord').findOne({ patientId });
      return patientRecord;
    } catch (error) {
      this.logger.error('Error getting patient record:', error);
      return null;
    }
  }

  private async updatePatientRecord(patientId: string, medicalHistory: string, insuranceClaims: string): Promise<PatientRecord> {
    try {
      const patientRecord = await mongoose.model('PatientRecord').findOneAndUpdate({ patientId }, { medicalHistory, insuranceClaims }, { new: true });
      return patientRecord;
    } catch (error) {
      this.logger.error('Error updating patient record:', error);
      throw error;
    }
  }

  private async deletePatientRecord(patientId: string): Promise<void> {
    try {
      await mongoose.model('PatientRecord').findOneAndDelete({ patientId });
    } catch (error) {
      this.logger.error('Error deleting patient record:', error);
      throw error;
    }
  }

  private async createSubscription(patientId: string, subscriptionStatus: string): Promise<Subscription> {
    try {
      const subscription = new mongoose.model('Subscription')({ patientId, subscriptionStatus });
      await subscription.save();
      return subscription;
    } catch (error) {
      this.logger.error('Error creating subscription:', error);
      throw error;
    }
  }

  private async getSubscription(subscriptionId: string): Promise<Subscription | null> {
    try {
      const subscription = await mongoose.model('Subscription').findOne({ subscriptionId });
      return subscription;
    } catch (error) {
      this.logger.error('Error getting subscription:', error);
      return null;
    }
  }

  private async updateSubscription(subscriptionId: string, subscriptionStatus: string): Promise<Subscription> {
    try {
      const subscription = await mongoose.model('Subscription').findOneAndUpdate({ subscriptionId }, { subscriptionStatus }, { new: true });
      return subscription;
    } catch (error) {
      this.logger.error('Error updating subscription:', error);
      throw error;
    }
  }

  private async deleteSubscription(subscriptionId: string): Promise<void> {
    try {
      await mongoose.model('Subscription').findOneAndDelete({ subscriptionId });
    } catch (error) {
      this.logger.error('Error deleting subscription:', error);
      throw error;
    }
  }
}

const healthcarePlatform = new HealthcarePlatform();
healthcarePlatform.start();