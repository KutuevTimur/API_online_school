import {
  TextInput,
  Textarea,
  type TextInputProps,
  type TextareaProps,
} from '@mantine/core';
export function FormField(props: TextInputProps) {
  return <TextInput {...props} />;
}
export function TextAreaField(props: TextareaProps) {
  return (
    <Textarea
      className="resize-none"
      style={{ resize: 'none' }}
      autosize
      minRows={4}
      {...props}
    />
  );
}
