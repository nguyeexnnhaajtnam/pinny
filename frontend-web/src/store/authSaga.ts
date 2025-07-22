import { call, put, takeLatest } from 'redux-saga/effects';
import axios, { AxiosResponse, AxiosError } from 'axios';
import {
  loginRequest,
  loginSuccess,
  loginFailure,
  logout,
  setToken,
  setError,
} from './authSlice';
import type { PayloadAction } from '@reduxjs/toolkit';

interface LoginPayload {
  email: string;
  password: string;
}

interface ErrorResponseData {
  error?: string;
  [key: string]: unknown;
}

function* handleLogin(action: PayloadAction<LoginPayload>): Generator<unknown, void, unknown> {
  try {
    const response = (yield call(axios.post, '/api/auth/login', action.payload)) as AxiosResponse;
    if (response.status === 200 && response.data.token) {
      yield put(loginSuccess({ user: response.data.user, token: response.data.token }));
      yield put(setToken(response.data.token));
      localStorage.setItem('token', response.data.token);
    } else {
      yield put(loginFailure((response.data as ErrorResponseData).error || 'Đăng nhập thất bại'));
      yield put(setError((response.data as ErrorResponseData).error || 'Đăng nhập thất bại'));
    }
  } catch (error: unknown) {
    const axiosError = error as AxiosError;
    const errMsg = (axiosError.response?.data as ErrorResponseData)?.error || 'Lỗi kết nối server';
    yield put(loginFailure(errMsg));
    yield put(setError(errMsg));
  }
}

function* handleLogout() {
  try {
    localStorage.removeItem('token');
    yield put(setToken(null));
  } catch {
    // ignore
  }
}

export default function* authSaga() {
  yield takeLatest(loginRequest.type, handleLogin);
  yield takeLatest(logout.type, handleLogout);
} 