# QR/SVD shifted-cocycle iteration

Initialize real subspaces from local SVDs, transport them through the cocycle,
interpolate from the shifted phase grid, and repeatedly orthonormalize and
align the resulting frames.  Stop at the frozen iteration cap or the principal-
angle tolerance; nonconvergence is a stored result, not a hidden retry.

