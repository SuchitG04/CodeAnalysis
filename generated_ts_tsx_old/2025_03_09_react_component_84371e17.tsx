import * as React from 'react';

interface Props {
  apiEndpoint: string;
  columns: string[];
  rowsPerPage: number;
  initialSortColumn: string;
  initialSortDirection: 'asc' | 'desc';
}

interface State {
  data: any[];
  error: string | null;
  loading: boolean;
  sortColumn: string;
  sortDirection: 'asc' | 'desc';
  page: number;
  rowsPerPage: number;
  selectedRows: any[];
  inlineEditRow: any | null;
}

class DataGrid extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      data: [],
      error: null,
      loading: false,
      sortColumn: props.initialSortColumn,
      sortDirection: props.initialSortDirection,
      page: 0,
      rowsPerPage: props.rowsPerPage,
      selectedRows: [],
      inlineEditRow: null,
    };
  }

  componentDidMount(): void {
    this.fetchData();
  }

  componentWillUnmount(): void {
    // Clean up any resources
  }

  fetchData = async (): Promise<void> => {
    this.setState({ loading: true });
    try {
      const response: AsyncResponse<PaginatedResponse<any>> = await fetch(
        `${this.props.apiEndpoint}?page=${this.state.page}&rowsPerPage=${this.state.rowsPerPage}&sortColumn=${this.state.sortColumn}&sortDirection=${this.state.sortDirection}`
      ).then((response) => response.json());
      if (response.error) {
        throw response.error;
      }
      this.setState({
        data: response.data.items,
        error: null,
        loading: false,
      });
    } catch (error) {
      this.setState({
        error: error.message,
        loading: false,
      });
    }
  };

  handleSort = (column: string): void => {
    this.setState({
      sortColumn: column,
      sortDirection: this.state.sortDirection === 'asc' ? 'desc' : 'asc',
    });
    this.fetchData();
  };

  handleFilter = (filter: string): void => {
    // Implement filtering logic
  };

  handlePageChange = (page: number): void => {
    this.setState({ page });
    this.fetchData();
  };

  handleRowsPerPageChange = (rowsPerPage: number): void => {
    this.setState({ rowsPerPage });
    this.fetchData();
  };

  handleRowSelect = (row: any): void => {
    const selectedRows = [...this.state.selectedRows];
    const index = selectedRows.indexOf(row);
    if (index === -1) {
      selectedRows.push(row);
    } else {
      selectedRows.splice(index, 1);
    }
    this.setState({ selectedRows });
  };

  handleInlineEdit = (row: any): void => {
    this.setState({ inlineEditRow: row });
  };

  handleInlineEditSave = (row: any): void => {
    // Implement logic to save inline edit changes
  };

  handleExport = (): void => {
    // Implement logic to export data
  };

  render(): JSX.Element {
    const { data, error, loading, sortColumn, sortDirection, page, rowsPerPage, selectedRows, inlineEditRow } = this.state;
    return (
      <div>
        {error && <div style={{ color: 'red' }}>{error}</div>}
        {loading && <div>Loading...</div>}
        <table>
          <thead>
            <tr>
              {this.props.columns.map((column) => (
                <th key={column}>
                  {column}
                  {sortColumn === column && (
                    <span>
                      {sortDirection === 'asc' ? '↑' : '↓'}
                    </span>
                  )}
                  <button onClick={() => this.handleSort(column)}>Sort</button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row) => (
              <tr key={row.id}>
                {this.props.columns.map((column) => (
                  <td key={column}>
                    {inlineEditRow === row ? (
                      <input
                        type="text"
                        value={row[column]}
                        onChange={(event) => this.handleInlineEditSave({ ...row, [column]: event.target.value })}
                      />
                    ) : (
                      row[column]
                    )}
                  </td>
                ))}
                <td>
                  <button onClick={() => this.handleRowSelect(row)}>Select</button>
                  <button onClick={() => this.handleInlineEdit(row)}>Edit</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div>
          <button onClick={() => this.handlePageChange(page - 1)}>Previous</button>
          <button onClick={() => this.handlePageChange(page + 1)}>Next</button>
          <select value={rowsPerPage} onChange={(event) => this.handleRowsPerPageChange(parseInt(event.target.value, 10))}>
            <option value="10">10</option>
            <option value="20">20</option>
            <option value="50">50</option>
          </select>
        </div>
        <button onClick={this.handleExport}>Export</button>
      </div>
    );
  }
}

export default DataGrid;