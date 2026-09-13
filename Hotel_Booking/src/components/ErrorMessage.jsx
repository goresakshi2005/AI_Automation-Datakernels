export default function ErrorMessage({ message, testId }) {
  if (!message) return null;

  return (
    <p className="form-error" data-testid={testId} role="alert">
      {message}
    </p>
  );
}
