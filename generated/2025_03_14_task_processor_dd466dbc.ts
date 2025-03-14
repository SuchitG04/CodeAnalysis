// Import necessary libraries and modules
import * as express from 'express';
import pgPromise from 'pg-promise';
import axios from 'axios';
import rateLimit from 'express-rate-limit';
import { v4 as uuidv4 } from 'uuid';

// Initialize pg-promise
const pgp = pgPromise();
const db = pgp('postgres://user:password@localhost:5432/financial_platform');

// Define interfaces for data structures
interface User {
    id: string;
    name: string;
    contact: string;
    roles: string[];
}

interface Payment {
    id: string;
    amount: number;
    method: string;
    userId: string;
}

interface InsuranceClaim {
    id: string;
    userId: string;
    amount: number;
    status: string;
}

// Adapter pattern for external integrations
class ExternalApiAdapter {
    async sendWebhook(data: any): Promise<void> {
        try {
            await axios.post('https://external-api.com/webhook', data);
        } catch (error) {
            console.error('Error sending webhook:', error);
        }
    }
}

// Main class to orchestrate data flow
class FinancialPlatform {
    private externalApiAdapter: ExternalApiAdapter;

    constructor() {
        this.externalApiAdapter = new ExternalApiAdapter();
    }

    // Middleware for API rate limiting
    rateLimitMiddleware(): express.RequestHandler {
        return rateLimit({
            windowMs: 15 * 60 * 1000, // 15 minutes
            max: 100, // limit each IP to 100 requests per windowMs
            message: 'Rate limit exceeded. Please try again later.'
        });
    }

    // Middleware for IP-based access restrictions
    ipAccessRestrictionMiddleware(allowedIPs: string[]): express.RequestHandler {
        return (req, res, next) => {
            if (!allowedIPs.includes(req.ip)) {
                return res.status(403).send('Access denied');
            }
            next();
        };
    }

    // Middleware for audit logging
    auditLoggingMiddleware(): express.RequestHandler {
        return (req, res, next) => {
            console.log(`Audit Log: ${req.method} ${req.url} by ${req.ip}`);
            next();
        };
    }

    // Middleware for form submission handling
    async handleFormSubmission(req: express.Request, res: express.Response): Promise<void> {
        const { userId, amount, method } = req.body;

        try {
            // Validate input
            if (!userId || !amount || !method) {
                throw new Error('Invalid input');
            }

            // Process payment
            const paymentId = uuidv4();
            const payment: Payment = { id: paymentId, amount, method, userId };
            await this.processPayment(payment);

            // Log successful payment
            console.log(`Payment processed: ${JSON.stringify(payment)}`);

            // Dispatch webhook for external systems
            await this.externalApiAdapter.sendWebhook(payment);

            res.status(200).send(`Payment ${paymentId} processed successfully`);
        } catch (error) {
            console.error('Error processing payment:', error);
            res.status(500).send('Internal server error');
        }
    }

    // Process payment and update database
    async processPayment(payment: Payment): Promise<void> {
        try {
            await db.none('INSERT INTO payments(id, amount, method, user_id) VALUES($1, $2, $3, $4)', [
                payment.id,
                payment.amount,
                payment.method,
                payment.userId
            ]);
        } catch (error) {
            console.error('Error inserting payment into database:', error);
            throw error;
        }
    }

    // Soft delete with audit trail
    async softDeleteUser(userId: string): Promise<void> {
        try {
            const auditId = uuidv4();
            await db.tx(async t => {
                await t.none('UPDATE users SET deleted_at = NOW() WHERE id = $1', [userId]);
                await t.none('INSERT INTO user_audit(id, user_id, action, timestamp) VALUES($1, $2, $3, NOW())', [auditId, userId, 'DELETE']);
            });
        } catch (error) {
            console.error('Error soft deleting user:', error);
            throw error;
        }
    }

    // Real-time data update using middleware
    realTimeDataUpdateMiddleware(): express.RequestHandler {
        return (req, res, next) => {
            // Simulate real-time data update
            console.log('Real-time data update triggered');
            next();
        };
    }

    // Start the Express server
    startServer(): void {
        const app = express();
        app.use(express.json());

        // Apply middleware
        app.use(this.rateLimitMiddleware());
        app.use(this.ipAccessRestrictionMiddleware(['127.0.0.1', '::1']));
        app.use(this.auditLoggingMiddleware());
        app.use(this.realTimeDataUpdateMiddleware());

        // Define routes
        app.post('/process-payment', this.handleFormSubmission.bind(this));

        // Start the server
        const PORT = process.env.PORT || 3000;
        app.listen(PORT, () => {
            console.log(`Server is running on port ${PORT}`);
        });
    }
}

// Create an instance of the FinancialPlatform and start the server
const platform = new FinancialPlatform();
platform.startServer();