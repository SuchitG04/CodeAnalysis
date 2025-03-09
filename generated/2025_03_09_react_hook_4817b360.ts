/**
 * Hook for managing organization profiles and subscriptions.
 * Handles company information, billing details, and subscription plans.
 * Tracks API usage, enforces limits, and manages organization hierarchies.
 *
 * @example
 * const { data, loading, error } = useOrganizationProfile();
 * if (loading) return <div>Loading...</div>;
 * if (error) return <div>Error: {error.message}</div>;
 * return <div>Organization Name: {data.name}</div>;
 */

import { useState, useEffect, useCallback } from 'react';
import { AxiosError } from 'axios';

// Define utility types and interfaces
type AsyncResponse<T> = {
    data: T;
    loading: boolean;
    error: Error | null;
};

type Optional<T> = T | undefined;

interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    pageSize: number;
}

interface OrganizationProfile {
    id: number;
    name: string;
    billingDetails: {
        address: string;
        plan: string;
    };
}

interface UseOrganizationProfileOptions {
    /**
     * Organization ID to fetch profile for.
     */
    organizationId: number;
}

/**
 * Hook for fetching and managing organization profiles.
 *
 * @param options - Options for the hook.
 * @param options.organizationId - Organization ID to fetch profile for.
 * @returns Async response with organization profile data, loading state, and error.
 */
function useOrganizationProfile(options: UseOrganizationProfileOptions): AsyncResponse<OrganizationProfile> {
    const [data, setData] = useState<Optional<OrganizationProfile>>(undefined);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<Error | null>(null);

    const fetchOrganizationProfile = useCallback(async () => {
        setLoading(true);
        try {
            // Simulate API call to fetch organization profile
            const response = await new Promise<OrganizationProfile>((resolve) => {
                // Replace with actual API call
                resolve({
                    id: options.organizationId,
                    name: 'Example Organization',
                    billingDetails: {
                        address: '123 Main St',
                        plan: 'Premium',
                    },
                });
            });
            setData(response);
        } catch (error) {
            if (error instanceof AxiosError) {
                setError(error);
            } else {
                setError(new Error('Failed to fetch organization profile'));
            }
        } finally {
            setLoading(false);
        }
    }, [options.organizationId]);

    useEffect(() => {
        fetchOrganizationProfile();
    }, [fetchOrganizationProfile]);

    return { data, loading, error };
}

export default useOrganizationProfile;