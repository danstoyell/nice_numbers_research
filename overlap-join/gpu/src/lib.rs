//! GPU (CubeCL 0.10) device stage of the overlap join for the public
//! nice-number client (wasabipesto/nice @ fe1b0b8). See join_kernels.rs.
pub mod client_check;
pub mod join_gpu;
pub mod join_kernels;
pub mod proto;
