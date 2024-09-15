// Copyright 2024 Google, LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
import { useContext, useState } from 'react';
import { BatchContext, SessionIDContext } from '../contexts';

import { OverridableStringUnion } from "@mui/types";
import { Container } from '@mui/system';
import {
  DataGrid,
  GridRowsProp,
  GridColDef,
  GridRowModesModel,
  GridToolbarContainer,
  GridRowModes,
  GridSlots,
  GridRowModel,
} from '@mui/x-data-grid';
import {
  Alert,
  AlertColor,
  AlertPropsColorOverrides,
  Box,
  Button,
  List,
  Paper,
  Snackbar,
  Step,
  StepLabel,
  Stepper,
} from '@mui/material';

import React from 'react';
import { useLoaderData } from 'react-router-dom';
import { BatchPromptRequest } from 'libs/model/src/lib/api';

import { BatchProductGridItem } from '../domain';
import AddIcon from '@mui/icons-material/Add';

const ProductAccordionPanel = React.lazy(() => import('../components/ProductAccordion'));

const columns: GridColDef[] = [
  { field: 'gtin', headerName: 'GTIN', width: 150, editable: true },
  { field: 'name', headerName: 'Name', width: 260, editable: true },
  { field: 'short_description', headerName: 'Short Description', display: 'flex', flex: 1, editable: true },
];

interface EditToolbarProps {
  rows: GridRowsProp[];
  setRows: (newRows: (oldRows: GridRowsProp) => GridRowsProp) => void;
  setRowModesModel: (newModel: (oldModel: GridRowModesModel) => GridRowModesModel) => void;
}

const GridToolbar = (props: EditToolbarProps) => {
  const { setRows, setRowModesModel, rows } = props;

  const handleAddClick = () => {
    const nextId = rows.length + 1;
    setRows((oldRows) => [...[{ id: nextId, gtin: '', name: '', short_description: '', isNew: true }], ...oldRows]);
    setRowModesModel((oldModel) => ({ ...oldModel, [nextId]: { mode: GridRowModes.Edit, fieldToFocus: 'name' } }));
  };

  return (
    <GridToolbarContainer sx={{ display: 'flex', flex: 1, alignItems: 'right', justifyContent: 'right' }}>
      <Button color="primary" startIcon={<AddIcon />} onClick={handleAddClick}>
        Add record
      </Button>
    </GridToolbarContainer>
  );
};



const BatchInputGrid = ({
  rows,
  setRows,
}: {
  rows: BatchProductGridItem[];
  setRows: (value: BatchProductGridItem[]) => void;
}) => {
  const [rowModesModel, setRowModesModel] = React.useState<GridRowModesModel>({});

  const processRowUpdate = (newRow: GridRowModel) => {
    const updatedRow = { ...newRow, isNew: false } as BatchProductGridItem;
    setRows(rows.map((row) => (row.id === newRow.id ? updatedRow : row)));
    return updatedRow;
  };

  return (
    <DataGrid
      rows={rows}
      columns={columns}
      processRowUpdate={processRowUpdate}
      slots={{
        toolbar: GridToolbar as GridSlots['toolbar'],
      }}
      slotProps={{
        toolbar: { setRows, setRowModesModel, rows: rows },
      }}
    />
  );
};

const Batch = () => {
  const data = useLoaderData();
  const { socket, products } = useContext(BatchContext);

  const [rows, setRows] = useState<BatchProductGridItem[]>(data as BatchProductGridItem[]);
  const { sessionID } = useContext(SessionIDContext);
  const [activeStep, setActiveStep] = useState(0);
  
  const [alertSeverity, setAlertSeverity] = useState<OverridableStringUnion<AlertColor, AlertPropsColorOverrides> | undefined>(undefined);
  const [snackBarMessage, setSnackBarMessage] = useState<string>('');
  const [showSnackBar, setShowSnackBar] = useState<boolean>(false);

  socket.on('batch:error', ({message}) => {
    setAlertSeverity('error');
    setSnackBarMessage(message);
    setShowSnackBar(true)
  });

  socket.on('batch:warn', ({message}) => {
    setAlertSeverity('warning');
    setSnackBarMessage(message);
    setShowSnackBar(true)
  });

  socket.on('batch:info', ({message}) => {
    setAlertSeverity('info');
    setSnackBarMessage(message);
    setShowSnackBar(true)
  });

  socket.on('batch:complete', ({message}) => {
    setAlertSeverity('success');
    setSnackBarMessage(message);
    setShowSnackBar(true)
  });
  

  const submit_batch = () => {
    socket.emit('batch:request', { sessionID: sessionID, values: rows } as BatchPromptRequest);
    setActiveStep(1);
  };

  const open_create = () => {
    setActiveStep(0);
  };

  const open_results = () => {
    if (products.length > 0) {
      setActiveStep(1);
    }
  };

  return (
    <Container>
      <Stepper activeStep={activeStep} sx={{ mb: 2 }}>
        <Step key="batch">
          <StepLabel onClick={open_create}>Create Batch</StepLabel>
        </Step>
        <Step key="review">
          <StepLabel onClick={open_results}>Batch Results</StepLabel>
        </Step>
      </Stepper>

      {activeStep === 0 ? (
        <React.Fragment>
          <BatchInputGrid rows={rows} setRows={setRows} />
          <Box sx={{ display: 'flex', flex: 1, justifyContent: 'right', mt: 2 }}>
            <Button onClick={submit_batch}>Submit</Button>
          </Box>
        </React.Fragment>
      ) : (
        <></>
      )}

      {activeStep === 1 ? (
        <React.Fragment>
          <List>
            {products.map((p, idx) => (
              <ProductAccordionPanel index={idx} product={p} />
            ))}
          </List>
        </React.Fragment>
      ) : (
        <></>
      )}
      <Snackbar
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        autoHideDuration={3000}
        open={showSnackBar}
        onClose={() => setShowSnackBar(false)}
        >
            <Alert
                onClose={() => setShowSnackBar(false)}
                severity={alertSeverity}
                variant="filled"
                sx={{ width: '100%' }}
            >
                {snackBarMessage}
            </Alert>
            </Snackbar>
    </Container>
  );
};

export default Batch;
