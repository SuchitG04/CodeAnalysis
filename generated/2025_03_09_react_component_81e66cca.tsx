/**
 * Represents the result of a validation process.
 * @template T The type of the data being validated.
 */
type ValidationResult<T> = {
    isValid: boolean;
    data?: T;
    errors?: Record<keyof T, string[]>;
};

/**
 * Represents an optional type.
 * @template T The type that can be optional.
 */
type Optional<T> = T | undefined;

/**
 * Represents the properties of a table component.
 * @template T The type of the data rows.
 */
interface TableProps<T> {
    data: T[];
    columns: ColumnDefinition<T>[];
    loading?: boolean;
    onSort?: (column: keyof T) => void;
    onRowClick?: (row: T) => void;
}

/**
 * Represents the definition of a column in a table.
 * @template T The type of the data rows.
 */
interface ColumnDefinition<T> {
    key: keyof T;
    label: string;
    sortable?: boolean;
}

/**
 * Represents a paginated response from a server.
 * @template T The type of the items in the response.
 */
interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    pageSize: number;
}