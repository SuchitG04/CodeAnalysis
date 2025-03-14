import { useState, useEffect, useRef } from 'react';
import axios from 'axios';

/**
 * Utility type for asynchronous responses.
 * @template T - The type of the data being fetched.
 */
type AsyncResponse<T> = {
    data: T;
    loading: boolean;
    error: Error | null;
};

/**
 * Utility type for form validation results.
 * @template T - The type of the form data being validated.
 */
type ValidationResult<T> = {
    isValid: boolean;
    data?: T;
    errors?: Record<keyof T, string[]>;
};

/**
 * BaseProps interface for common component properties.
 */
interface BaseProps {
    className?: string;
    style?: React.CSSProperties;
    children?: React.ReactNode;
}

/**
 * Interface for the form data.
 */
interface PaymentFormData {
    amount: number;
    currency: string;
    method: string;
    invoiceId: string;
}

/**
 * Custom React hook for handling financial data and form validation.
 * @param url - The URL to fetch financial data from.
 * @param initialData - Initial form data.
 * @returns An object containing the form state, validation results, and methods to handle form changes and submission.
 */
function useFinancialForm<T extends PaymentFormData>(url: string, initialData: T): AsyncResponse<T> & ValidationResult<T> & {
    handleChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    handleSubmit: (e: React.FormEvent) => void;
} {
    const [data, setData] = useState<T>(initialData);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<Error | null>(null);
    const [isValid, setIsValid] = useState<boolean>(false);
    const [errors, setErrors] = useState<Record<keyof T, string[]>>({});

    const isMounted = useRef<boolean>(true);

    useEffect(() => {
        return () => {
            isMounted.current = false;
        };
    }, []);

    /**
     * Fetch financial data from the provided URL.
     * @param url - The URL to fetch data from.
     * @returns A promise that resolves to the fetched data.
     */
    const fetchData = async (url: string): Promise<T> => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.get<T>(url);
            if (isMounted.current) {
                setData(response.data);
            }
            return response.data;
        } catch (err) {
            if (isMounted.current) {
                setError(err as Error);
            }
            throw err;
        } finally {
            if (isMounted.current) {
                setLoading(false);
            }
        }
    };

    /**
     * Validate the form data.
     * @returns A ValidationResult object containing the validation status, data, and errors.
     */
    const validateForm = (): ValidationResult<T> => {
        const newErrors: Record<keyof T, string[]> = {
            amount: [],
            currency: [],
            method: [],
            invoiceId: [],
        };

        if (data.amount <= 0) {
            newErrors.amount.push('Amount must be greater than zero.');
        }

        if (data.currency !== 'USD' && data.currency !== 'EUR') {
            newErrors.currency.push('Currency must be USD or EUR.');
        }

        if (data.method !== 'credit_card' && data.method !== 'bank_transfer') {
            newErrors.method.push('Payment method must be credit_card or bank_transfer.');
        }

        if (data.invoiceId.length !== 10) {
            newErrors.invoiceId.push('Invoice ID must be 10 characters long.');
        }

        const formIsValid = Object.values(newErrors).every(fieldErrors => fieldErrors.length === 0);
        setErrors(newErrors);
        setIsValid(formIsValid);

        return {
            isValid: formIsValid,
            data: formIsValid ? data : undefined,
            errors: newErrors,
        };
    };

    /**
     * Handle changes in form input fields.
     * @param e - The change event from the input field.
     */
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setData(prevData => ({ ...prevData, [name]: value as any }));
    };

    /**
     * Handle form submission.
     * @param e - The form submission event.
     */
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const validation = validateForm();
        if (validation.isValid) {
            try {
                await fetchData(url);
                console.log('Form submitted successfully with data:', data);
            } catch (err) {
                console.error('Error submitting form:', err);
            }
        } else {
            console.log('Form submission failed with errors:', validation.errors);
        }
    };

    return {
        data,
        loading,
        error,
        isValid,
        errors,
        handleChange,
        handleSubmit,
    };
}

// Example usage
interface PaymentFormProps extends BaseProps {
    onSubmit: (data: PaymentFormData) => void;
}

const PaymentForm: React.FC<PaymentFormProps> = ({ onSubmit, className, style, children }) => {
    const initialData: PaymentFormData = {
        amount: 0,
        currency: 'USD',
        method: 'credit_card',
        invoiceId: '',
    };

    const {
        data,
        loading,
        error,
        isValid,
        errors,
        handleChange,
        handleSubmit,
    } = useFinancialForm<PaymentFormData>('https://api.example.com/financial-data', initialData);

    return (
        <form className={className} style={style} onSubmit={handleSubmit}>
            <div>
                <label htmlFor="amount">Amount:</label>
                <input
                    type="number"
                    id="amount"
                    name="amount"
                    value={data.amount}
                    onChange={handleChange}
                />
                {errors.amount && errors.amount.map((err, index) => (
                    <p key={index} style={{ color: 'red' }}>{err}</p>
                ))}
            </div>
            <div>
                <label htmlFor="currency">Currency:</label>
                <input
                    type="text"
                    id="currency"
                    name="currency"
                    value={data.currency}
                    onChange={handleChange}
                />
                {errors.currency && errors.currency.map((err, index) => (
                    <p key={index} style={{ color: 'red' }}>{err}</p>
                ))}
            </div>
            <div>
                <label htmlFor="method">Payment Method:</label>
                <input
                    type="text"
                    id="method"
                    name="method"
                    value={data.method}
                    onChange={handleChange}
                />
                {errors.method && errors.method.map((err, index) => (
                    <p key={index} style={{ color: 'red' }}>{err}</p>
                ))}
            </div>
            <div>
                <label htmlFor="invoiceId">Invoice ID:</label>
                <input
                    type="text"
                    id="invoiceId"
                    name="invoiceId"
                    value={data.invoiceId}
                    onChange={handleChange}
                />
                {errors.invoiceId && errors.invoiceId.map((err, index) => (
                    <p key={index} style={{ color: 'red' }}>{err}</p>
                ))}
            </div>
            <button type="submit" disabled={!isValid || loading}>
                {loading ? 'Submitting...' : 'Submit'}
            </button>
            {children}
        </form>
    );
};

export default PaymentForm;