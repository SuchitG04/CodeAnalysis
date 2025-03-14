/**
 * @module FinancialDataHandler
 * @description This module handles data aggregation, processing, and storage in a financial platform.
 * It includes security and compliance measures, error handling, and monitoring.
 */

import * as archiver from 'archiver';
import * as fs from 'fs';
import * as path from 'path';
import { AuthAdapter } from './adapters/AuthAdapter';
import { UserProfileAdapter } from './adapters/UserProfileAdapter';
import { PerformanceMetricsAdapter } from './adapters/PerformanceMetricsAdapter';
import { EventLoggingAdapter } from './adapters/EventLoggingAdapter';
import { RateLimiter } from './RateLimiter';
import { HIPAACompliantAccessControl } from './HIPAACompliantAccessControl';
import { DataBreachNotifier } from './DataBreachNotifier';
import { Logger } from './Logger';

/**
 * Main class to orchestrate data flow in the financial platform.
 */
class FinancialDataHandler {
    private authAdapter: AuthAdapter;
    private userProfileAdapter: UserProfileAdapter;
    private performanceMetricsAdapter: PerformanceMetricsAdapter;
    private eventLoggingAdapter: EventLoggingAdapter;
    private rateLimiter: RateLimiter;
    private accessControl: HIPAACompliantAccessControl;
    private dataBreachNotifier: DataBreachNotifier;
    private logger: Logger;

    constructor() {
        this.authAdapter = new AuthAdapter();
        this.userProfileAdapter = new UserProfileAdapter();
        this.performanceMetricsAdapter = new PerformanceMetricsAdapter();
        this.eventLoggingAdapter = new EventLoggingAdapter();
        this.rateLimiter = new RateLimiter();
        this.accessControl = new HIPAACompliantAccessControl();
        this.dataBreachNotifier = new DataBreachNotifier();
        this.logger = new Logger();
    }

    /**
     * Orchestrates the data flow in the financial platform.
     * @async
     * @throws {Error} If any data source or sink operation fails.
     */
    public async processDataFlow(): Promise<void> {
        try {
            // Rate limiting and quota enforcement
            if (!this.rateLimiter.isRequestAllowed()) {
                throw new Error('API rate limit exceeded');
            }

            // Fetch data from external sources
            const tokens = await this.authAdapter.getTokens();
            const userProfiles = await this.userProfileAdapter.getUserProfiles();
            const performanceMetrics = await this.performanceMetricsAdapter.getPerformanceMetrics();
            const events = await this.eventLoggingAdapter.getEvents();

            // Aggregate and process data
            const aggregatedData = this.aggregateData(tokens, userProfiles, performanceMetrics, events);

            // Data sink operations
            await this.storeAggregatedData(aggregatedData);

            // Monitoring
            this.logger.log('Data processing completed successfully');
        } catch (error) {
            this.logger.error(`Error in data processing: ${error.message}`);
            if (error.message.includes('API rate limit exceeded')) {
                this.logger.warn('Rate limit exceeded, notifying admin');
            } else {
                this.dataBreachNotifier.notifyDataBreach(error.message);
            }
        }
    }

    /**
     * Aggregates data from various sources.
     * @param {string[]} tokens - Authentication tokens.
     * @param {object[]} userProfiles - User profiles.
     * @param {object} performanceMetrics - Performance metrics.
     * @param {object[]} events - Event logs.
     * @returns {object} Aggregated data.
     */
    private aggregateData(tokens: string[], userProfiles: object[], performanceMetrics: object, events: object[]): object {
        // Implement data aggregation logic here
        return {
            tokens,
            userProfiles,
            performanceMetrics,
            events,
        };
    }

    /**
     * Stores aggregated data in a secure and compliant manner.
     * @param {object} aggregatedData - Aggregated data to be stored.
     * @async
     * @throws {Error} If data storage fails.
     */
    private async storeAggregatedData(aggregatedData: object): Promise<void> {
        try {
            // Ensure HIPAA-compliant access controls
            if (!this.accessControl.isAccessAllowed()) {
                throw new Error('Access denied due to HIPAA compliance');
            }

            // Write data to a temporary file
            const tempFilePath = path.join(__dirname, 'temp', 'aggregated_data.json');
            fs.writeFileSync(tempFilePath, JSON.stringify(aggregatedData));

            // Compress the file using archiver
            const output = fs.createWriteStream(path.join(__dirname, 'temp', 'aggregated_data.zip'));
            const archive = archiver('zip', {
                zlib: { level: 9 }, // Set the compression level
            });

            output.on('close', () => {
                this.logger.log(`Data compressed to ${archive.pointer()} total bytes`);
                // Clean up the temporary file
                fs.unlinkSync(tempFilePath);
            });

            archive.on('error', (err) => {
                throw err;
            });

            archive.pipe(output);
            archive.file(tempFilePath, { name: 'aggregated_data.json' });
            await archive.finalize();
        } catch (error) {
            this.logger.error(`Error storing aggregated data: ${error.message}`);
            throw error;
        }
    }
}

// Example usage
const dataHandler = new FinancialDataHandler();
dataHandler.processDataFlow().then(() => {
    console.log('Data flow processed');
}).catch((error) => {
    console.error(`Error in data flow processing: ${error.message}`);
});