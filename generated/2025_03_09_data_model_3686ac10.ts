/**
 * File: metricsCollector.ts
 * Description: This file is part of a larger project that collects and analyzes system-wide metrics.
 * It demonstrates data handling in a security-sensitive environment.
 */

import * as express from 'express';
import * as jwt from 'jsonwebtoken';
import * as fs from 'fs-extra';
import * as path from 'path';
import * as axios from 'axios';
import { PubSub } from 'graphql-subscriptions';
import { v4 as uuidv4 } from 'uuid';

// Stubbed external dependencies
const authService = {
  validateToken: (token: string): Promise<boolean> => {
    return new Promise((resolve) => {
      // Simulate token validation
      resolve(token === 'valid_token');
    });
  },
};

const subscriptionManagementSystem = {
  getUserSubscriptions: (userId: string): Promise<string[]> => {
    return new Promise((resolve) => {
      // Simulate fetching user subscriptions
      resolve(['subscription1', 'subscription2']);
    });
  },
};

const apiGateway = {
  sendGraphQLMutation: async (mutation: string, variables: any): Promise<any> => {
    try {
      const response = await axios.post('https://api.example.com/graphql', {
        query: mutation,
        variables,
      });
      return response.data;
    } catch (error) {
      console.error('GraphQL mutation failed:', error);
      throw error;
    }
  },
};

// Constants
const JWT_SECRET = 'secret_key';
const FILE_PATH = path.join(__dirname, 'metrics.log');
const DATA_RETENTION_DAYS = 30;

// Pub/Sub for real-time event logging
const pubsub = new PubSub();

// Events
const EVENTS = {
  NEW_METRIC: 'NEW_METRIC',
};

/**
 * MetricsCollector class orchestrates the data flow, handles data sources,
 * and ensures security and compliance.
 */
class MetricsCollector {
  private logger: any;

  constructor() {
    this.logger = this.setupLogger();
  }

  /**
   * Sets up a simple file-based logger.
   * @returns A logger object.
   */
  private setupLogger(): any {
    return {
      info: (message: string) => this.logToFile('INFO', message),
      error: (message: string) => this.logToFile('ERROR', message),
    };
  }

  /**
   * Logs a message to a file with a timestamp.
   * @param level - Log level (INFO, ERROR, etc.)
   * @param message - Log message
   */
  private logToFile(level: string, message: string): void {
    const timestamp = new Date().toISOString();
    const logMessage = `${timestamp} [${level}]: ${message}\n`;
    fs.appendFileSync(FILE_PATH, logMessage);
  }

  /**
   * Validates the JWT token using the Authentication Service.
   * @param token - JWT token
   * @returns A promise that resolves to a boolean indicating whether the token is valid.
   */
  private async validateJWTToken(token: string): Promise<boolean> {
    try {
      const isValid = await authService.validateToken(token);
      if (!isValid) {
        this.logger.error('Invalid JWT token');
      }
      return isValid;
    } catch (error) {
      this.logger.error('Token validation failed:', error);
      throw error;
    }
  }

  /**
   * Handles the authentication flow using Express middleware.
   * @param req - Express request object
   * @param res - Express response object
   * @param next - Next middleware function
   */
  public authenticate = async (req: express.Request, res: express.Response, next: express.NextFunction): Promise<void> => {
    const authHeader = req.headers.authorization;
    if (!authHeader) {
      res.status(401).send('No token provided');
      return;
    }

    const token = authHeader.split(' ')[1];
    try {
      const isValid = await this.validateJWTToken(token);
      if (!isValid) {
        res.status(401).send('Invalid token');
        return;
      }

      // Decode token to get user roles
      const decoded = jwt.verify(token, JWT_SECRET) as { userId: string; roles: string[] };
      req.user = decoded;
      next();
    } catch (error) {
      res.status(403).send('Failed to authenticate token');
    }
  };

  /**
   * Collects metrics from various data sources and publishes them.
   * @param userId - User ID
   * @param metrics - Metrics data
   */
  public collectMetrics = async (userId: string, metrics: any): Promise<void> => {
    try {
      const subscriptions = await subscriptionManagementSystem.getUserSubscriptions(userId);
      if (subscriptions.length === 0) {
        this.logger.info(`No subscriptions found for user ${userId}`);
        return;
      }

      // Publish metrics to subscribers
      pubsub.publish(EVENTS.NEW_METRIC, { newMetric: { userId, metrics, subscriptions } });
      this.logger.info(`Metrics collected for user ${userId}`);
    } catch (error) {
      this.logger.error('Failed to collect metrics:', error);
    }
  };

  /**
   * Handles real-time event logging using Pub/Sub.
   */
  public setupEventLogging(): void {
    pubsub.subscribe(EVENTS.NEW_METRIC, ({ newMetric }) => {
      this.logToFile('METRIC', JSON.stringify(newMetric));
      this.sendMetricsToExternalAPI(newMetric);
    });
  }

  /**
   * Sends metrics to an external API using GraphQL mutations.
   * @param metrics - Metrics data
   */
  private async sendMetricsToExternalAPI(metrics: any): Promise<void> {
    const mutation = `
      mutation SendMetrics($metrics: MetricsInput!) {
        sendMetrics(metrics: $metrics) {
          success
          message
        }
      }
    `;

    try {
      await apiGateway.sendGraphQLMutation(mutation, { metrics });
      this.logger.info('Metrics sent to external API successfully');
    } catch (error) {
      this.logger.error('Failed to send metrics to external API:', error);
      // Retry logic can be implemented here
    }
  }

  /**
   * Implements data retention policies.
   */
  public enforceDataRetention(): void {
    const retentionPeriod = DATA_RETENTION_DAYS * 24 * 60 * 60 * 1000;
    const now = new Date().getTime();

    fs.readFile(FILE_PATH, 'utf8', (err, data) => {
      if (err) {
        this.logger.error('Failed to read metrics file:', err);
        return;
      }

      const lines = data.split('\n').filter((line) => line.trim());
      const filteredLines = lines.filter((line) => {
        const timestamp = new Date(line.split(' ')[0]).getTime();
        return now - timestamp < retentionPeriod;
      });

      fs.writeFile(FILE_PATH, filteredLines.join('\n'), (err) => {
        if (err) {
          this.logger.error('Failed to write filtered metrics file:', err);
        }
      });
    });
  }
}

// Example usage
const app = express();
const metricsCollector = new MetricsCollector();

// Middleware for authentication
app.use(metricsCollector.authenticate);

// Endpoint to collect metrics
app.post('/metrics', (req, res) => {
  const { userId, metrics } = req.body;
  metricsCollector.collectMetrics(userId, metrics);
  res.status(200).send('Metrics collected');
});

// Setup event logging
metricsCollector.setupEventLogging();

// Enforce data retention policies
setInterval(metricsCollector.enforceDataRetention, 24 * 60 * 60 * 1000); // Run daily

// Start the server
app.listen(3000, () => {
  console.log('Metrics collector server running on port 3000');
});