// Import necessary modules
import * as fs from 'fs-extra';
import * as crypto from 'crypto';
import * as path from 'path';
import { EventEmitter } from 'events';

// Stubbed external dependencies
const FinancialLedgerDatabase = {
  getProfileUpdates: () => Promise.resolve([{ userId: '123', updateType: 'profile' }]),
  getSubscriptionChanges: () => Promise.resolve([{ userId: '123', changeType: 'subscription' }]),
};

const InsuranceClaimsDatabase = {
  getClaimsData: () => Promise.resolve([{ claimId: '456', amount: 1000 }]),
};

const ComplianceDataWarehouse = {
  getComplianceData: () => Promise.resolve([{ userId: '123', complianceStatus: 'compliant' }]),
};

// Event-driven architecture setup
const eventEmitter = new EventEmitter();

// Constants
const LOG_DIR = path.join(__dirname, 'logs');
const LOG_FILE_PREFIX = 'system_metrics_';
const ENCRYPTION_KEY = crypto.randomBytes(32); // 256-bit key
const IV_LENGTH = 16;

// Utility functions
function encrypt(text: string, key: Buffer, iv: Buffer): string {
  const cipher = crypto.createCipheriv('aes-256-cbc', Buffer.from(key), iv);
  let encrypted = cipher.update(text, 'utf8', 'hex');
  encrypted += cipher.final('hex');
  return iv.toString('hex') + ':' + encrypted;
}

function decrypt(text: string, key: Buffer): string {
  const textParts = text.split(':');
  const iv = Buffer.from(textParts.shift(), 'hex');
  const encryptedText = textParts.join(':');
  const decipher = crypto.createDecipheriv('aes-256-cbc', Buffer.from(key), iv);
  let decrypted = decipher.update(encryptedText, 'hex', 'utf8');
  decrypted += decipher.final('utf8');
  return decrypted;
}

// Data sink operations
class LogFile {
  private currentLogFile: string;
  private logFileIndex: number;

  constructor() {
    this.logFileIndex = 0;
    this.currentLogFile = this.getLogFileName();
    fs.ensureDirSync(LOG_DIR);
  }

  private getLogFileName(): string {
    return path.join(LOG_DIR, `${LOG_FILE_PREFIX}${this.logFileIndex}.log`);
  }

  private rotateLogFile(): void {
    this.logFileIndex += 1;
    this.currentLogFile = this.getLogFileName();
  }

  async writeLog(data: string): Promise<void> {
    try {
      const logData = encrypt(data, ENCRYPTION_KEY, crypto.randomBytes(IV_LENGTH));
      await fs.appendFile(this.currentLogFile, logData + '\n');
      const stats = await fs.stat(this.currentLogFile);
      if (stats.size > 1024 * 1024) { // Rotate log file if it exceeds 1MB
        this.rotateLogFile();
      }
    } catch (error) {
      console.error('Error writing log:', error);
    }
  }
}

// Main class orchestrating the data flow
class DataHandler {
  private logFile: LogFile;

  constructor() {
    this.logFile = new LogFile();
    this.setupEventListeners();
  }

  private setupEventListeners(): void {
    eventEmitter.on('profileUpdate', this.handleProfileUpdate.bind(this));
    eventEmitter.on('subscriptionChange', this.handleSubscriptionChange.bind(this));
    eventEmitter.on('claimsData', this.handleClaimsData.bind(this));
    eventEmitter.on('complianceData', this.handleComplianceData.bind(this));
  }

  private async handleProfileUpdate(data: any): Promise<void> {
    try {
      if (!data.userId || !data.updateType) throw new Error('Invalid data format');
      await this.logFile.writeLog(JSON.stringify(data));
      console.log('Profile update handled:', data);
    } catch (error) {
      console.error('Error handling profile update:', error);
    }
  }

  private async handleSubscriptionChange(data: any): Promise<void> {
    try {
      if (!data.userId || !data.changeType) throw new Error('Invalid data format');
      await this.logFile.writeLog(JSON.stringify(data));
      console.log('Subscription change handled:', data);
    } catch (error) {
      console.error('Error handling subscription change:', error);
    }
  }

  private async handleClaimsData(data: any): Promise<void> {
    try {
      if (!data.claimId || !data.amount) throw new Error('Invalid data format');
      await this.logFile.writeLog(JSON.stringify(data));
      console.log('Claims data handled:', data);
    } catch (error) {
      console.error('Error handling claims data:', error);
    }
  }

  private async handleComplianceData(data: any): Promise<void> {
    try {
      if (!data.userId || !data.complianceStatus) throw new Error('Invalid data format');
      await this.logFile.writeLog(JSON.stringify(data));
      console.log('Compliance data handled:', data);
    } catch (error) {
      console.error('Error handling compliance data:', error);
    }
  }

  async fetchData(): Promise<void> {
    try {
      const profileUpdates = await FinancialLedgerDatabase.getProfileUpdates();
      profileUpdates.forEach((update) => eventEmitter.emit('profileUpdate', update));

      const subscriptionChanges = await FinancialLedgerDatabase.getSubscriptionChanges();
      subscriptionChanges.forEach((change) => eventEmitter.emit('subscriptionChange', change));

      const claimsData = await InsuranceClaimsDatabase.getClaimsData();
      claimsData.forEach((claim) => eventEmitter.emit('claimsData', claim));

      const complianceData = await ComplianceDataWarehouse.getComplianceData();
      complianceData.forEach((compliance) => eventEmitter.emit('complianceData', compliance));
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  }
}

// Main function to run the data handler
async function main(): Promise<void> {
  const dataHandler = new DataHandler();
  await dataHandler.fetchData();
}

// Run the main function
main().catch((error) => console.error('Main function error:', error));