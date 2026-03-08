type FieldLike = {
  name: string
  state: {
    value: unknown
    meta: {
      isTouched: boolean
      errors: Array<unknown>
    }
  }
  handleBlur: () => void
  handleChange: (value: string) => void
}

type Props = {
  field: FieldLike
  label: string
  type?: string
  placeholder?: string
  autoComplete?: string
  autoFocus?: boolean
}

export function FormField({
  field,
  label,
  type = 'text',
  placeholder,
  autoComplete,
  autoFocus,
}: Props) {
  const errors = field.state.meta.errors
  const hasError = field.state.meta.isTouched && errors.length > 0

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={field.name} className="text-sm text-gray-300">
        {label}
      </label>
      <input
        id={field.name}
        name={field.name}
        type={type}
        placeholder={placeholder}
        autoComplete={autoComplete}
        autoFocus={autoFocus}
        value={field.state.value as string}
        onBlur={field.handleBlur}
        onChange={(e) => field.handleChange(e.target.value)}
        className={[
          'w-full px-3 py-2.5 rounded-lg bg-gray-800 border text-white text-sm placeholder-gray-500 focus:outline-none focus:border-indigo-500',
          hasError ? 'border-red-500' : 'border-gray-700',
        ].join(' ')}
      />
      {hasError && <p className="text-red-400 text-xs">{String(errors[0])}</p>}
    </div>
  )
}
