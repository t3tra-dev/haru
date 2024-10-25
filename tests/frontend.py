from haru.ui import Element, Props, create_element

view: Element = create_element(
    'div',
    props=Props(className='view', id='view'),
    children=[
        create_element(
            'h1',
            props=Props(className='title'),
            children=['Hello, World!']
        ),
        create_element(
            'button',
            props=Props(className='button', onClick=lambda: print('Button clicked!')),
            children=['Click Me']
        )
    ]
)

view.render()
