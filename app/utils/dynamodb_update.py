
class DynamodbUpdate:
    def __init__(self):
        self._add = set([])
        self._set = set([])
        self._delete = set([])
        self._parameter_names = []
        self._parameter_values = {}
        self._parameter_count = 0

    def set(self, field, value):
        key = self._register_parameter_name(field)
        if key is not None:
            self._set.add('#{key} = :{key}'.format(key=key))
            self._parameter_values[':' + key] = value

    def add(self, field, value):
        key = self._register_parameter_name(field)
        if key is not None:
            self._add.add('#{key} = :{key}'.format(key=key))
            value = set(value) if isinstance(value, list) else value
            self._parameter_values[':' + key] = value

    def delete(self, field, value):
        key = self._register_parameter_name(field)
        if key is not None:
            self._delete.add('#{key} = :{key}'.format(key=key))
            self._parameter_values[':' + key] = value

    @property
    def update_expression(self):
        set_str = 'SET {}'.format(', '.join(self._set)) if len(self._set) else ''
        add_str = 'ADD {}'.format(', '.join(self._add)) if len(self._add) else ''
        del_str = 'DELETE {}'.format(', '.join(self._delete)) if len(self._delete) else ''
        return set_str + ' ' + add_str + ' ' + del_str

    @property
    def parameter_names(self):
        return {'#p' + str(i): n for i, n in enumerate(self._parameter_names)}

    @property
    def parameter_values(self):
        return self._parameter_values

    def _register_parameter_name(self, parameter_name):
        if parameter_name in self._parameter_names:
            return None
        self._parameter_names.append(parameter_name)
        return 'p' + str(len(self._parameter_names) - 1)

    def __str__(self):
        return str({
            'update_expression': self.update_expression,
            'parameter_names': self.parameter_names,
            'parameter_values': self.parameter_values,
        })
