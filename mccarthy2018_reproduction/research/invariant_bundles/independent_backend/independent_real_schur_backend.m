function independent_real_schur_backend(input_path, output_path, log_path)
%INDEPENDENT_REAL_SCHUR_BACKEND Independent MATLAB real-Schur validation.
%   The input contains real collocation operators assembled by the frozen
%   Python research pipeline.  Spectral selection and invariant-subspace
%   construction are performed here with MATLAB SCHUR/ORDSCHUR.  No NumPy
%   eigensolver output is supplied to this function.

diary(log_path);
cleanup = onCleanup(@() diary('off')); %#ok<NASGU>
fprintf('independent_real_schur_backend start=%s\n', datestr(now, 30));
fprintf('input=%s\noutput=%s\n', input_path, output_path);

payload = load(input_path);
operators = payload.operators;
case_ids = payload.case_ids;
hyperbolic_tolerance = double(payload.hyperbolic_tolerance(1));
near_axis_tie_tolerance = double(payload.near_axis_tie_tolerance(1));
n_cases = numel(operators);

bases = cell(1, n_cases);
selected_blocks = cell(1, n_cases);
selected_spectra = cell(1, n_cases);
dimensions = zeros(1, n_cases);
relative_imaginary = nan(1, n_cases);
partial_schur_residual = nan(1, n_cases);
orthogonality_residual = nan(1, n_cases);
runtime_seconds = nan(1, n_cases);
errors = cell(1, n_cases);

for index = 1:n_cases
    case_id = char(case_ids{index});
    started = tic;
    try
        A = double(operators{index});
        if size(A, 1) ~= size(A, 2) || ~isreal(A)
            error('independent_schur:invalidOperator', ...
                'Operator for %s must be a real square matrix.', case_id);
        end
        [U, T] = schur(A, 'real');
        lambda = ordeig(T);
        candidates = find(abs(lambda) > 1.0 + hyperbolic_tolerance);
        if isempty(candidates)
            error('independent_schur:noUnstableSpectrum', ...
                'No unstable hyperbolic spectrum for %s.', case_id);
        end
        candidate_relative_imaginary = abs(imag(lambda(candidates))) ./ ...
            max(abs(lambda(candidates)), realmin('double'));
        minimum_imaginary = min(candidate_relative_imaginary);
        near_axis = candidates(candidate_relative_imaginary <= ...
            minimum_imaginary + near_axis_tie_tolerance);
        [~, local_index] = max(abs(lambda(near_axis)));
        target_index = near_axis(local_index);

        block_tolerance = 100.0 * eps(max(1.0, norm(T, 'fro')));
        if target_index < size(T, 1) && ...
                abs(T(target_index + 1, target_index)) > block_tolerance
            block_indices = [target_index, target_index + 1];
        elseif target_index > 1 && ...
                abs(T(target_index, target_index - 1)) > block_tolerance
            block_indices = [target_index - 1, target_index];
        else
            block_indices = target_index;
        end

        select = false(size(T, 1), 1);
        select(block_indices) = true;
        [U_ordered, T_ordered] = ordschur(U, T, select);
        selected_dimension = numel(block_indices);
        Q_selected = U_ordered(:, 1:selected_dimension);
        T_selected = T_ordered(1:selected_dimension, 1:selected_dimension);
        spectrum = eig(T_selected);
        defect = A * Q_selected - Q_selected * T_selected;

        bases{index} = Q_selected;
        selected_blocks{index} = T_selected;
        selected_spectra{index} = spectrum;
        dimensions(index) = selected_dimension;
        relative_imaginary(index) = max(abs(imag(spectrum)) ./ ...
            max(abs(spectrum), realmin('double')));
        partial_schur_residual(index) = norm(defect, 'fro') / ...
            max(norm(A * Q_selected, 'fro'), realmin('double'));
        orthogonality_residual(index) = norm( ...
            Q_selected' * Q_selected - eye(selected_dimension), 'fro');
        errors{index} = '';
        runtime_seconds(index) = toc(started);
        fprintf(['case=%s dimension=%d rel_imag=%.17g schur_residual=%.17g ' ...
            'orthogonality=%.17g runtime=%.9f status=ok\n'], ...
            case_id, selected_dimension, relative_imaginary(index), ...
            partial_schur_residual(index), orthogonality_residual(index), ...
            runtime_seconds(index));
    catch exception
        runtime_seconds(index) = toc(started);
        errors{index} = getReport(exception, 'extended', 'hyperlinks', 'off');
        fprintf('case=%s runtime=%.9f status=error\n%s\n', ...
            case_id, runtime_seconds(index), errors{index});
    end
end

matlab_version = version;
matlab_release = version('-release');
computer_architecture = computer;
blas_lapack_info = evalc('version -blas');
schema_version = 'independent_matlab_real_schur_backend_v1';
completed_utc = datestr(now, 30);
save(output_path, 'schema_version', 'completed_utc', 'case_ids', 'bases', ...
    'selected_blocks', 'selected_spectra', 'dimensions', ...
    'relative_imaginary', 'partial_schur_residual', ...
    'orthogonality_residual', 'runtime_seconds', 'errors', ...
    'matlab_version', 'matlab_release', 'computer_architecture', ...
    'blas_lapack_info', '-v7');
fprintf('independent_real_schur_backend complete=%s cases=%d\n', ...
    completed_utc, n_cases);
end
