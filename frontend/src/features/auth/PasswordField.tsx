import { useState, forwardRef } from 'react';
import { PasswordInput, type PasswordInputProps } from '@mantine/core';
export const PasswordField = forwardRef<HTMLInputElement, PasswordInputProps>(
  function PasswordField(props, ref) {
    const [visible, setVisible] = useState(false);
    return (
      <PasswordInput
        {...props}
        ref={ref}
        visible={visible}
        rightSectionWidth={44}
        visibilityToggleFocusable
        onVisibilityChange={setVisible}
        visibilityToggleButtonProps={{
          'aria-label': visible ? 'Скрыть пароль' : 'Показать пароль',
          'aria-pressed': visible,
          style: { minWidth: 44, minHeight: 44, width: 44, height: 44 },
        }}
      />
    );
  },
);
